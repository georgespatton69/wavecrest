"""
Meta Marketing API integration for Wavecrest.

Pulls ad performance data and leads from Meta (Facebook/Instagram) Ads.

Requirements:
    - META_ACCESS_TOKEN in .env (System User token with ads_read + leads_retrieval)
    - META_AD_ACCOUNT_ID in .env (format: act_XXXXXXXXX)
    - META_PAGE_ID in .env (for lead forms)

Usage:
    from meta_api import MetaAPI
    api = MetaAPI()
    if api.is_configured():
        api.sync_campaigns()
        api.sync_leads()
"""

import os
import sys
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helpers import execute_query, insert_row

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


class MetaAPI:
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN", "").strip()
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID", "").strip()
        self.page_id = os.getenv("META_PAGE_ID", "").strip()

    def is_configured(self):
        """Check if all required credentials are set."""
        return bool(self.access_token and self.ad_account_id)

    def is_leads_configured(self):
        """Check if lead retrieval credentials are set."""
        return bool(self.access_token and self.page_id)

    def _get(self, endpoint, params=None):
        """Make a GET request to the Meta Graph API."""
        if params is None:
            params = {}
        params["access_token"] = self.access_token

        url = f"{BASE_URL}/{endpoint}"
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _get_all_pages(self, endpoint, params=None):
        """Fetch all pages of a paginated response."""
        results = []
        if params is None:
            params = {}
        params["access_token"] = self.access_token

        url = f"{BASE_URL}/{endpoint}"
        while url:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = {}  # next URL includes params
        return results

    # ----- Campaign / Ad Set / Ad sync -----

    def sync_campaigns(self):
        """Pull all campaigns from Meta and sync to local DB."""
        campaigns = self._get_all_pages(
            f"{self.ad_account_id}/campaigns",
            params={
                "fields": "name,objective,status,daily_budget,lifetime_budget,start_time,stop_time",
                "limit": 100,
            },
        )

        synced = 0
        for camp in campaigns:
            meta_id = camp["id"]
            existing = execute_query(
                "SELECT id FROM ad_campaigns WHERE meta_campaign_id = ?", [meta_id]
            )

            status_map = {"ACTIVE": "active", "PAUSED": "paused", "ARCHIVED": "completed", "DELETED": "completed"}
            camp_status = status_map.get(camp.get("status", ""), "active")

            # Budget from Meta is in cents
            daily_budget = float(camp.get("daily_budget", 0)) / 100 if camp.get("daily_budget") else None
            lifetime_budget = float(camp.get("lifetime_budget", 0)) / 100 if camp.get("lifetime_budget") else None

            start_date = camp.get("start_time", "")[:10] or None
            end_date = camp.get("stop_time", "")[:10] or None

            if existing:
                execute_query(
                    "UPDATE ad_campaigns SET name=?, objective=?, status=?, daily_budget=?, "
                    "lifetime_budget=?, start_date=?, end_date=?, updated_at=CURRENT_TIMESTAMP "
                    "WHERE meta_campaign_id=?",
                    [camp["name"], camp.get("objective"), camp_status,
                     daily_budget, lifetime_budget, start_date, end_date, meta_id],
                )
            else:
                insert_row("ad_campaigns", {
                    "meta_campaign_id": meta_id,
                    "name": camp["name"],
                    "objective": camp.get("objective"),
                    "status": camp_status,
                    "daily_budget": daily_budget,
                    "lifetime_budget": lifetime_budget,
                    "start_date": start_date,
                    "end_date": end_date,
                })
            synced += 1

            # Sync ad sets for this campaign
            self._sync_ad_sets(meta_id)

        return synced

    def _sync_ad_sets(self, meta_campaign_id):
        """Pull ad sets for a campaign."""
        ad_sets = self._get_all_pages(
            f"{meta_campaign_id}/adsets",
            params={
                "fields": "name,status,targeting",
                "limit": 100,
            },
        )

        # Get local campaign ID
        camp_rows = execute_query(
            "SELECT id FROM ad_campaigns WHERE meta_campaign_id = ?", [meta_campaign_id]
        )
        if not camp_rows:
            return
        local_camp_id = camp_rows[0]["id"]

        status_map = {"ACTIVE": "active", "PAUSED": "paused", "ARCHIVED": "completed", "DELETED": "completed"}

        for aset in ad_sets:
            meta_id = aset["id"]
            existing = execute_query(
                "SELECT id FROM ad_sets WHERE meta_adset_id = ?", [meta_id]
            )

            aset_status = status_map.get(aset.get("status", ""), "active")
            targeting = str(aset.get("targeting", ""))[:500] if aset.get("targeting") else None

            if existing:
                execute_query(
                    "UPDATE ad_sets SET name=?, status=?, targeting_summary=? WHERE meta_adset_id=?",
                    [aset["name"], aset_status, targeting, meta_id],
                )
            else:
                insert_row("ad_sets", {
                    "campaign_id": local_camp_id,
                    "meta_adset_id": meta_id,
                    "name": aset["name"],
                    "status": aset_status,
                    "targeting_summary": targeting,
                })

            # Sync ads for this ad set
            self._sync_ads(meta_id)

    def _sync_ads(self, meta_adset_id):
        """Pull ads for an ad set."""
        ads = self._get_all_pages(
            f"{meta_adset_id}/ads",
            params={
                "fields": "name,status,creative{body,title}",
                "limit": 100,
            },
        )

        aset_rows = execute_query(
            "SELECT id FROM ad_sets WHERE meta_adset_id = ?", [meta_adset_id]
        )
        if not aset_rows:
            return
        local_aset_id = aset_rows[0]["id"]

        status_map = {"ACTIVE": "active", "PAUSED": "paused", "ARCHIVED": "completed", "DELETED": "completed"}

        for ad in ads:
            meta_id = ad["id"]
            existing = execute_query(
                "SELECT id FROM ads WHERE meta_ad_id = ?", [meta_id]
            )

            ad_status = status_map.get(ad.get("status", ""), "active")
            creative = ad.get("creative", {})
            creative_summary = creative.get("title", "") or creative.get("body", "")
            if creative_summary:
                creative_summary = creative_summary[:200]

            if existing:
                execute_query(
                    "UPDATE ads SET name=?, status=?, creative_summary=? WHERE meta_ad_id=?",
                    [ad["name"], ad_status, creative_summary or None, meta_id],
                )
            else:
                insert_row("ads", {
                    "ad_set_id": local_aset_id,
                    "meta_ad_id": meta_id,
                    "name": ad["name"],
                    "status": ad_status,
                    "creative_summary": creative_summary or None,
                })

    # ----- Metrics sync -----

    def sync_metrics(self, days=7):
        """Pull daily metrics for all campaigns for the last N days."""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")

        campaigns = execute_query("SELECT id, meta_campaign_id FROM ad_campaigns WHERE meta_campaign_id IS NOT NULL")

        synced = 0
        for camp in campaigns:
            if not camp["meta_campaign_id"]:
                continue

            try:
                insights = self._get_all_pages(
                    f"{camp['meta_campaign_id']}/insights",
                    params={
                        "fields": "spend,impressions,clicks,actions,ctr,cpc,cpm",
                        "time_range": f'{{"since":"{since}","until":"{until}"}}',
                        "time_increment": 1,
                        "limit": 100,
                    },
                )
            except requests.HTTPError:
                continue

            for day in insights:
                metric_date = day.get("date_start", "")[:10]
                if not metric_date:
                    continue

                spend = float(day.get("spend", 0))
                impressions = int(day.get("impressions", 0))
                clicks = int(day.get("clicks", 0))
                ctr = float(day.get("ctr", 0))
                cpc = float(day.get("cpc", 0))
                cpm = float(day.get("cpm", 0))

                # Extract conversions from actions
                conversions = 0
                for action in day.get("actions", []):
                    if action.get("action_type") in ("lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"):
                        conversions += int(action.get("value", 0))

                # Upsert: delete existing + insert
                execute_query(
                    "DELETE FROM ad_metrics WHERE campaign_id = ? AND metric_date = ? AND ad_set_id IS NULL AND ad_id IS NULL",
                    [camp["id"], metric_date],
                )
                insert_row("ad_metrics", {
                    "campaign_id": camp["id"],
                    "metric_date": metric_date,
                    "spend": spend,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "ctr": ctr,
                    "cpc": cpc,
                    "cpm": cpm,
                })
                synced += 1

        return synced

    # ----- Leads sync -----

    def sync_leads(self):
        """Pull leads from all lead gen forms on the Page."""
        if not self.is_leads_configured():
            return 0

        # Get all lead forms for the page
        try:
            forms = self._get_all_pages(
                f"{self.page_id}/leadgen_forms",
                params={"fields": "id,name,status", "limit": 100},
            )
        except requests.HTTPError:
            return 0

        synced = 0
        for form in forms:
            form_id = form["id"]
            form_name = form.get("name", "")

            try:
                leads = self._get_all_pages(
                    f"{form_id}/leads",
                    params={"fields": "created_time,field_data,ad_id,ad_name,campaign_id,campaign_name", "limit": 100},
                )
            except requests.HTTPError:
                continue

            for lead_data in leads:
                meta_lead_id = lead_data["id"]

                # Check if already imported (use created_time + name as dedup)
                field_map = {}
                for field in lead_data.get("field_data", []):
                    field_map[field["name"].lower()] = field["values"][0] if field.get("values") else ""

                name = field_map.get("full_name") or field_map.get("first_name", "") + " " + field_map.get("last_name", "")
                name = name.strip()
                email = field_map.get("email", "")
                phone = field_map.get("phone_number") or field_map.get("phone", "")

                if not name:
                    name = email or f"Lead #{meta_lead_id}"

                # Dedup by email or phone + form
                if email:
                    existing = execute_query(
                        "SELECT id FROM leads WHERE email = ? AND form_name = ?",
                        [email, form_name],
                    )
                elif phone:
                    existing = execute_query(
                        "SELECT id FROM leads WHERE phone = ? AND form_name = ?",
                        [phone, form_name],
                    )
                else:
                    existing = execute_query(
                        "SELECT id FROM leads WHERE name = ? AND form_name = ? AND source = 'meta_ads'",
                        [name, form_name],
                    )

                if existing:
                    continue

                new_id = insert_row("leads", {
                    "name": name,
                    "email": email or None,
                    "phone": phone or None,
                    "source": "meta_ads",
                    "campaign_name": lead_data.get("campaign_name"),
                    "ad_name": lead_data.get("ad_name"),
                    "form_name": form_name,
                    "stage": "new",
                })
                insert_row("lead_activity", {
                    "lead_id": new_id,
                    "action": "Lead imported",
                    "details": f"Auto-imported from Meta form: {form_name}",
                })
                synced += 1

        return synced


def sync_all():
    """Run a full sync of campaigns, metrics, and leads."""
    api = MetaAPI()
    results = {}

    if api.is_configured():
        results["campaigns"] = api.sync_campaigns()
        results["metrics"] = api.sync_metrics(days=30)
    else:
        results["campaigns"] = "Not configured"
        results["metrics"] = "Not configured"

    if api.is_leads_configured():
        results["leads"] = api.sync_leads()
    else:
        results["leads"] = "Not configured"

    return results


if __name__ == "__main__":
    import json
    results = sync_all()
    print(json.dumps(results, indent=2))
