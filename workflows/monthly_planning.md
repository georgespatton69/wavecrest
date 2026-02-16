# Monthly Content Planning Session

## Objective
Plan the full month of social media content for @wavecrestbehavioral on Instagram and Facebook. Target: 3-4 posts per week across both platforms.

## When
First working day of each month, during a Claude Code session.

## Required Inputs
- Previous month's performance data (from Meta API or dashboard Analytics page)
- New therapist interview scripts (from the monthly recorded interview)
- New UGC scripts/ideas from UGC creator
- Any current business priorities, promotions, or announcements
- Relevant dates and awareness days for the month (e.g., Mental Health Awareness Month, holidays)

## Content Pillars
| Pillar | Description | Target Mix |
|--------|-------------|-----------|
| Education | Mental health tips, coping strategies, treatment info | ~30% |
| Affirming Messages | Positive, supportive quotes and messages | ~25% |
| Community | SoCal lifestyle, team highlights, behind-the-scenes | ~20% |
| Client Stories | UGC content, testimonials (with consent) | ~15% |
| Treatment Info | Virtual IOP details, how to get help, insurance info | ~10% |

## Content Types
- **Still Images** — Educational graphics, affirming quotes, tips (branded templates)
- **Therapist Videos** — Clips from monthly therapist interview (Reels/short-form)
- **UGC Videos** — Content from UGC creator (lifestyle, day-in-the-life, tips)
- **Carousels** — Multi-slide educational content
- **Stories** — Behind-the-scenes, polls, engagement content

## Process

### Step 1: Performance Review (15 min)
1. Open the dashboard: `streamlit run dashboard/app.py`
2. Go to **Analytics** page — review last month's metrics
3. Note what performed well and what didn't
4. If Meta API is connected:
   - Run `python3 tools/meta_fetch_insights.py --snapshot`
   - Run `python3 tools/meta_fetch_posts.py --save`
5. Key questions to answer:
   - Which content type got the most engagement?
   - What posting times worked best?
   - Which pillars resonated most?

### Step 2: Competitor Check (10 min)
1. Open Charlie Health's Instagram (@charliehealth) and Novara's (@novararecoverycenter)
2. Go to **Competitors** page in the dashboard
3. Log current follower counts using the snapshot form
4. Note 2-3 standout posts from each competitor and log them
5. Key questions:
   - Any new content formats they're trying?
   - What topics are getting high engagement?
   - Anything we should adapt for our audience?

### Step 3: Script Review (15 min)
1. Go to **Scripts** page in the dashboard
2. **Therapist scripts:** Add all clips/ideas from this month's interview
   - Title each script clearly (e.g., "3 Anxiety Coping Techniques")
   - Tag with the right pillar
   - Set session date to the interview date
3. **UGC scripts:** Add any new ideas from the UGC creator
4. Review all draft scripts and mark the best ones as "Selected" for this month
5. Archive any old scripts that are no longer relevant

### Step 4: Idea Generation (10 min)
1. Go to **Ideas** page in the dashboard
2. Review existing ideas in the bank (especially "Developing" column)
3. Brainstorm new ideas based on:
   - Competitor inspiration
   - Trending topics in mental health
   - Seasonal/calendar relevance
   - Gaps in our content mix
4. Add new ideas with appropriate pillars and priorities

### Step 5: Build the Calendar (20 min)
1. Go to **Calendar** page in the dashboard
2. Target: 3-4 posts per week (12-16 posts for the month)
3. Posting schedule suggestion:
   - **Monday:** Educational content (start the week with value)
   - **Wednesday:** Therapist video or UGC (mid-week engagement)
   - **Friday:** Affirming message or community content (end-of-week positivity)
   - **Optional Saturday:** Story or additional content
4. For each post, fill in:
   - Date and time
   - Platform (Instagram, Facebook, or both)
   - Content type
   - Pillar
   - Caption
   - Hashtags
5. Ensure good variety across the month — don't cluster same types together
6. Cross-post to both platforms when appropriate (not always — vary captions)

### Step 6: Review & Finalize (5 min)
1. Check the calendar grid view — does it look balanced?
2. Run `python3 tools/calendar_manager.py summary --month YYYY-MM --pretty`
3. Verify:
   - Content mix aligns with target percentages
   - No gaps of 3+ days without a post
   - Both platforms are covered
   - All content pillars are represented
4. Make any final adjustments

## Expected Outputs
- Populated content calendar for the month (visible in dashboard)
- Scripts marked with correct statuses (selected for this month)
- Updated idea bank
- Competitor snapshots logged
- Optional: Performance analysis documented

## Hashtag Strategy
Core hashtags to rotate:
- `#virtualIOP` `#virtualtherapy` `#mentalhealthmatters`
- `#orangecounty` `#socal` `#californiarecovery`
- `#anxietyrelief` `#depressionhelp` `#traumarecovery`
- `#mentalhealthtips` `#selfcare` `#recovery`
- `#wavecrestbehavioral` (branded)

Mix 5-10 hashtags per post. Use a combination of broad reach + niche tags.

## Edge Cases
- **No therapist interview this month:** Rely on backlog scripts and increase UGC/still image content
- **Meta API token expired:** Run `python3 tools/meta_auth.py refresh` or manually log metrics on the Analytics page
- **Holiday or awareness day mid-month:** Create timely content (plan 1 week ahead when possible)
- **Low content ideas:** Run competitor check more thoroughly; look at trending mental health topics
- **Content underperforming:** Review analytics for patterns, adjust content mix for next month

## Style Guidelines
- **Tone:** Warm, calming, professional but approachable. Southern California energy.
- **Visual:** Clean, minimal, coastal color palette. ASMR-peaceful aesthetic.
- **Voice:** "We understand. We're here to help." — never clinical or cold.
- **Accessibility:** Alt text on images, captions on videos, readable fonts on graphics.
