# 📊 EXCEL REPORT DESIGN - Business Intelligence Mapping

## DATA SOURCES & AVAILABILITY

### ✅ **WHAT WE HAVE:**

#### **A. Instagram Raw Data** (from JSON scraper):
```
Per Post:
├─ Post Metadata
│  ├─ id, shortCode, url
│  ├─ timestamp (date/time)
│  ├─ type (Image, Video, Sidecar)
│  └─ location {name, id}
│
├─ User/Influencer Info
│  ├─ ownerUsername
│  ├─ ownerFullName
│  ├─ ownerId
│  └─ [NO follower count in dataset]
│
├─ Engagement Metrics
│  ├─ likesCount (or -1 if hidden)
│  ├─ commentsCount
│  ├─ videoViewCount (for videos)
│  └─ [NO reach/impressions data]
│
├─ Content
│  ├─ caption (text)
│  ├─ hashtags []
│  ├─ mentions []
│  └─ alt text
│
├─ Media
│  ├─ displayUrl (main image)
│  ├─ videoUrl (if video)
│  ├─ childPosts [] (carousel images)
│  └─ dimensions (height, width)
│
└─ Comments
   ├─ latestComments [] (up to ~20)
   │  ├─ text
   │  ├─ ownerUsername
   │  ├─ timestamp
   │  └─ likesCount
   └─ firstComment (caption-like comment)
```

#### **B. LLM Analysis Output** (from vision model):
```json
{
  "nicotine_detection": {
    "detected": true/false,
    "confidence": "high"/"medium"/"low",
    "products": [
      {
        "category": "IQOS"/"glo"/"Ploom"/"Cigarette"/"Vape"/"Nicotine_Pouch"/etc,
        "specific_brand": "Terea Turquoise",
        "specific_model": "IQOS ILUMA PRIME",
        "product_type": "Device"/"Consumable"/"Both",
        "quantity_visible": "single"/"multiple",
        "visual_prominence": "primary_focus"/"secondary"/"background"
      }
    ],
    "detection_evidence": {
      "visual": ["what LLM saw in images"],
      "caption": ["quotes from caption"],
      "comments": ["relevant comment mentions"],
      "hashtags": ["relevant hashtags"]
    },
    "usage_context": "Dining_Casual"/"Nightlife_Bar"/"Event_CuriousX"/etc,
    "usage_type": "Active_Use"/"Product_Display"/"Unboxing"/etc,
    "co_occurrence": {
      "food_beverage": true/false,
      "alcohol": true/false,
      "other_tobacco": true/false
    }
  },

  "sentiment": {
    "overall": "positive"/"neutral"/"negative"/"mixed",
    "confidence": "high"/"medium"/"low",
    "dimensions": {
      "product_quality": {"sentiment": "positive", "evidence": "..."},
      "social_acceptance": {...},
      "health_perception": {...},
      "value_price": {...},
      "convenience": {...}
    },
    "key_phrases": ["quotes"],
    "language_tone": "casual"/"formal"/"enthusiastic",
    "emoji_usage": {"present": true, "tone": "positive", "examples": ["🔥"]}
  },

  "competitive_intelligence": {
    "brand_comparison_present": true/false,
    "brands_compared": ["IQOS", "glo"],
    "switching_behavior": {
      "detected": true/false,
      "from_product": "Cigarette",
      "to_product": "IQOS",
      "reason_mentioned": "health concerns",
      "evidence": "quote"
    },
    "competitor_activity": [{type, brand, evidence}],
    "price_mentions": {present, details},
    "availability_mentions": {present, details}
  },

  "content_analysis": {
    "primary_category": "Dining"/"Nightlife"/"Travel"/etc,
    "secondary_categories": ["Social", "Lifestyle"],
    "content_themes": ["celebration", "luxury"],
    "setting": "Restaurant_Interior",
    "time_of_day": "evening",
    "formality": "casual",
    "occasion_type": "birthday",
    "people_count": "2-3",
    "visual_quality": "high_amateur",
    "aesthetic_style": "candid"
  },

  "account_signals": {
    "user_type_indicators": ["Lifestyle_Influencer", "Regular_IQOS_User"],
    "content_style": "Authentic"/"Promotional",
    "engagement_pattern": "high_engagement",
    "brand_affinity": {
      "iqos": "strong_positive",
      "competitors": "neutral"
    },
    "partnership_potential": {
      "rating": "high"/"medium"/"low",
      "reasoning": "explanation",
      "red_flags": []
    }
  },

  "hashtag_analysis": {
    "hashtags_present": ["#tbilisi", "#nightlife"],
    "branded_hashtags": ["#iqos"],
    "campaign_hashtags": [],
    "reach_potential": "high"/"medium"/"low"
  },

  "metadata": {
    "primary_language": "georgian"/"english",
    "secondary_language": null,
    "image_count_analyzed": 4,
    "comment_count_analyzed": 18,
    "analysis_confidence": "high",
    "ambiguities": [],
    "analysis_notes": "..."
  }
}
```

---

## ⚠️ **WHAT WE DON'T HAVE (Missing from Dataset):**

### **Critical Gaps:**

1. **Follower Counts** - No follower data for influencers
   - Impact: Cannot calculate engagement rate (likes/followers)
   - Impact: Cannot rank influencers by reach
   - Workaround: Use post engagement as proxy (likes + comments)

2. **Historical Trend Data** - Only current snapshot, no time series
   - Dataset: May 2023 - Oct 2025 (but mixed, not ordered chronologically)
   - Impact: Can't show "Share of Voice trending up 15% this quarter"
   - Workaround: Group by month using timestamp field

3. **Impressions/Reach** - No data on who SAW posts
   - Only have likes/comments (engagement)
   - Cannot calculate true "Share of Voice by impressions"
   - Workaround: Use "Share of Mentions" instead

4. **Demographic Data** - No age, gender, location of users
   - Only have location tags on some posts (not user demographics)
   - Cannot say "15-25 age group prefers vapes"
   - Workaround: Infer from content_analysis themes

---

## 📊 **8-SHEET REPORT DESIGN - FEASIBILITY ANALYSIS**

### **Sheet 1: Executive Summary** ✅ FULLY FEASIBLE

**Data Available:**
```
┌─ Quick Metrics
│  ├─ Total Posts Analyzed: 2,629
│  ├─ Detection Rate: X% (nicotine_detection.detected count / total)
│  ├─ IQOS Share of Mentions: X% (category=="IQOS" / total detections)
│  └─ Top Competitor: glo/Ploom (from category counts)
│
├─ Top 3 Insights (manual curation + evidence links)
│  └─ Extracted from competitive_intelligence + sentiment
│
└─ Top 10 Influencers (by posts analyzed + detection %)
   ├─ @username (from ownerUsername)
   ├─ Posts: count
   ├─ IQOS mentions: X
   └─ [LINK to All Posts sheet filtered by user]
```

**Charts:**
- Pie: Share of Mentions by category (IQOS, glo, Ploom, Cigarette, Vape, Pouches)
- Bar: Detection rate by category

---

### **Sheet 2: Share of Voice** ⚠️ PARTIALLY FEASIBLE

**What We CAN Do:**
```
Category          Posts  % of Detections
────────────────────────────────────────
IQOS              XX     XX%
glo               XX     XX%
Ploom             XX     XX%
Cigarettes        XX     XX%
Vapes             XX     XX%
Nicotine Pouches  XX     XX%
```

**Trend Over Time (Monthly):**
```python
# Group by timestamp field
posts_by_month = group_by(timestamp[:7])  # YYYY-MM
detections_by_category_by_month = ...

Chart: Line graph showing IQOS vs glo vs Ploom mentions per month
```

**What We CANNOT Do:**
- "Weighted by engagement" - we don't have follower counts for true engagement rate
- Trend analysis requires enough data per month (may be sparse in 2,629 posts)

**Workaround:**
- Use "Share of Mentions" instead of "Share of Voice"
- Weight by likes + comments as proxy for reach

---

### **Sheet 3: IQOS Performance** ✅ FULLY FEASIBLE

**Data Available:**
```
Product Breakdown:
├─ From specific_brand field:
│  ├─ Terea (count, avg sentiment)
│  ├─ Heets (count, avg sentiment)
│  ├─ ILUMA devices (count)
│  └─ Delia (count)
│
├─ Sentiment Analysis (from sentiment.dimensions):
│  ├─ Product Quality: X% positive
│  ├─ Social Acceptance: X% positive
│  ├─ Health Perception: X% positive
│  ├─ Value/Price: X% neutral / negative
│  └─ Convenience: X% positive
│
├─ Usage Context Distribution (from usage_context):
│  ├─ Dining: 45%
│  ├─ Nightlife: 30%
│  ├─ Events: 15%
│  └─ Home: 10%
│
└─ Top Posts (highest engagement IQOS posts)
   ├─ Sorted by: likesCount + commentsCount
   └─ Link to post URL
```

**Evidence Links:**
- All cells link to "Sheet 8: Post Database" with filters

---

### **Sheet 4: Competitive Intelligence** ✅ FULLY FEASIBLE

**Data Available:**
```
glo Activity:
├─ Post count (category == "glo")
├─ Sponsored content detection
│  └─ From: metadata.is_sponsored OR partnership_potential OR content_style=="Promotional"
├─ Event partnerships
│  └─ From: usage_context=="Event_Branded" + competitor_activity field
├─ Price mentions
│  └─ From: competitive_intelligence.price_mentions.details
└─ Evidence links to posts

Switching Signals:
├─ From: competitive_intelligence.switching_behavior
│  ├─ Cigarette → IQOS: count + reasons
│  ├─ Cigarette → glo: count
│  └─ IQOS → glo: count (concerning!)
└─ Evidence quotes from switching_behavior.evidence

Vape Threat:
├─ Vape mention count (category=="Vape")
├─ Co-occurrence with certain content themes
├─ Sentiment comparison (vapes vs HNB)
└─ Youth appeal indicators from content_analysis
```

---

### **Sheet 5: Influencer Intelligence** ⚠️ PARTIALLY FEASIBLE

**What We CAN Do:**
```
Username         Posts  IQOS%  Sentiment  Partnership  Evidence
────────────────────────────────────────────────────────────────
@nick_noza       120    75%    Positive   HIGH         [link]
@ratisbar        89     45%    Positive   MEDIUM       [link]
```

**Calculations:**
- Username: from ownerUsername
- Posts: count of posts by this user
- IQOS%: (IQOS detections / total posts by user) * 100
- Sentiment: avg(sentiment.overall) for IQOS posts
- Partnership Potential: from account_signals.partnership_potential.rating
- Evidence: link to filtered post list

**What We CANNOT Do:**
- Engagement Rate = likes / followers (no follower data)
- True "reach" metrics

**Workaround:**
- Use "Avg Engagement per Post" = avg(likesCount + commentsCount)
- Add column: "Content Quality" from account_signals.content_style

---

### **Sheet 6: Media Landscape** ✅ FULLY FEASIBLE

**Data Available:**
```
Category        Posts  Nicotine%  IQOS%  Top Context
──────────────────────────────────────────────────────
Dining           892   35%        18%    Casual (from content_analysis.primary_category + formality)
Nightlife        654   42%        22%    Bars
Lifestyle        420   28%        15%    Home
Events           198   55%        30%    Branded events
Travel           165   15%        8%     Vacation

Derived from:
- content_analysis.primary_category
- content_analysis.content_themes
- content_analysis.setting
- usage_context field
```

---

### **Sheet 7: Hashtag Analysis** ✅ FULLY FEASIBLE

**Data Available:**
```
Hashtag          Posts  IQOS%  Avg Engagement  Opportunity
──────────────────────────────────────────────────────────
#tbilisi         450    12%    235 (avg likes) HIGH
#nightlife       320    25%    189             HIGH
#smokefree       89     45%    156             OWN THIS
#iqos            67     100%   98              Saturated

From:
- hashtags[] field (Instagram data)
- hashtag_analysis.hashtags_present
- likesCount + commentsCount (engagement)
- Join with nicotine_detection to calc IQOS%
```

**Co-occurrence Network:**
```python
# Find hashtag combinations that appear together
# When IQOS is detected, which other hashtags present?
co_occurrence_matrix = ...
```

---

### **Sheet 8: Detailed Post Database** ✅ FULLY FEASIBLE

**All Fields Available:**
```
30+ columns:
├─ Post URL (clickable) - from url field
├─ @Username (clickable) - from ownerUsername
├─ Full Name - from ownerFullName
├─ Date - from timestamp
├─ Type - from type (Image/Video/Sidecar)
├─ Caption - from caption
├─ Hashtags - from hashtags[]
├─ Likes - from likesCount
├─ Comments Count - from commentsCount
├─ Location - from location.name
│
├─ Nicotine Detected (Y/N) - from nicotine_detection.detected
├─ Confidence - from nicotine_detection.confidence
├─ Product Category - from products[0].category
├─ Specific Brand - from products[0].specific_brand
├─ Specific Model - from products[0].specific_model
│
├─ Sentiment Overall - from sentiment.overall
├─ Sentiment: Quality - from sentiment.dimensions.product_quality
├─ Sentiment: Social - from sentiment.dimensions.social_acceptance
├─ Sentiment: Health - from sentiment.dimensions.health_perception
├─ Sentiment: Price - from sentiment.dimensions.value_price
├─ Sentiment: Convenience - from sentiment.dimensions.convenience
│
├─ Usage Context - from usage_context
├─ Usage Type - from usage_type
├─ Content Category - from content_analysis.primary_category
├─ Setting - from content_analysis.setting
│
├─ Visual Evidence - from detection_evidence.visual
├─ Text Evidence - from detection_evidence.caption + comments
├─ Partnership Potential - from account_signals.partnership_potential.rating
│
└─ Image Links (clickable thumbnails) - from displayUrl, childPosts[].displayUrl
```

**Features:**
- Filter any column
- Sort by any metric
- Search text (Excel native)
- Conditional formatting for detections
- Color-code by sentiment

---

## 🎯 **IMPLEMENTATION PRIORITY**

### **Phase 1: Core Validation Report** (for 50-post sample)
1. ✅ Sheet 1: Executive Summary (simple metrics)
2. ✅ Sheet 2: Detected Posts (evidence validation)
3. ✅ Sheet 3: All Posts Database (spot-checking)

### **Phase 2: Full Business Intelligence** (for 2,629-post production)
4. Sheet 1: Executive Summary (enhanced with insights)
5. Sheet 2: Share of Mentions (with monthly trends)
6. Sheet 3: IQOS Performance (product/sentiment deep dive)
7. Sheet 4: Competitive Intelligence (threat radar)
8. Sheet 5: Influencer Intelligence (partnership database)
9. Sheet 6: Media Landscape (content intelligence)
10. Sheet 7: Hashtag Analysis (organic reach opportunities)
11. Sheet 8: Detailed Post Database (raw evidence)

---

## ❓ **QUESTIONS FOR YOU:**

1. **Follower Data:** Do you have access to follower counts for these influencers from another source?
   - If yes, we can join it for engagement rate calculations
   - If no, we use "Avg Engagement per Post" as proxy

2. **Time Granularity:** For trend analysis, should we:
   - Group by month (YYYY-MM)?
   - Group by quarter (Q1 2023, Q2 2023, etc.)?
   - Skip trends if data is too sparse?

3. **Competitive Focus:** Which competitors matter most for reporting?
   - glo (main threat)?
   - Ploom (emerging)?
   - Traditional cigarettes (baseline)?
   - Vapes (different category)?
   - Nicotine pouches (new trend)?

4. **Validation Threshold:** For the 50-post sample, is 0% false positive rate required, or is 1-2% acceptable if we can verify they're "borderline" cases?

5. **Evidence Depth:** In the influencer/competitive sheets, how much evidence do you want?
   - Just counts + one example link?
   - Full list of links to all relevant posts?
   - Screenshots/thumbnails embedded?

---

## 💡 **RECOMMENDATIONS:**

### **Given Data Constraints:**

1. **Use "Share of Mentions" not "Share of Voice"**
   - We have mention counts, not reach/impressions
   - Transparent and defensible metric

2. **Engagement Proxy: Likes + Comments**
   - Since no follower data: rank influencers by avg engagement
   - Label as "Engagement per Post" not "Engagement Rate"

3. **Temporal Analysis: Monthly Grouping**
   - Dataset spans 30 months (May 2023 - Oct 2025)
   - Group by month, show trend lines
   - Caveat: Some months may be sparse

4. **Evidence-First Approach**
   - Every metric links to source posts
   - Stakeholder can verify any claim
   - Builds trust in LLM-generated insights

5. **Conditional Formatting for Actionability**
   - Green: High partnership potential
   - Yellow: Monitor
   - Red: Competitor user / Avoid

---

## 🚀 **NEXT STEPS:**

Once Run #3 completes:
1. Validate 0% false positive rate
2. You answer the 5 questions above
3. I implement full 8-sheet report builder
4. Run on 2,629 posts overnight
5. Deliver actionable business intelligence Excel workbook

**Ready to build when you give the go-ahead!**
