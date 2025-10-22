# Prompt Refinement Log
**Date:** October 22, 2025, 19:45
**Analysis Running:** Posts 13+ (in progress)

---

## REFINEMENTS APPLIED

### 1. Multilingual Processing (Lines 18-21)

**Problem:** Original prompt was underspecified about Georgian vs English handling, creating implicit English preference.

**Before:**
```
5. Handle both Georgian and English text naturally
```

**After:**
```
2. Process ALL languages and scripts equally (Georgian, English, mixed/transliterated text)
   - Accept Georgian Mkhedruli script (ა-ჰ)
   - Accept transliteration (e.g., "gilocavt" for "გილოცავთ")
   - No preference for English - treat all scripts as primary sources
```

**Impact:**
- Removes implicit English bias
- Explicitly supports transliteration
- Enables true multilingual reasoning instead of English fallback

---

### 2. Brand Detection Rules (Lines 43-83)

**Problem:** Confusion between "no keyword matching" and legitimate textual evidence from captions/comments.

**Before:**
```
ONLY detect if you see SPECIFIC brand indicators:
  * Brand text visible (IQOS, ILUMA, TEREA, DELIA, glo, Neo, Ploom, cigarette pack logos)
```

**After:**
```
BRAND TEXT/LOGO DETECTION RULES - ALL must be true:
  A. Visual Evidence (Physical Object):
     * At least 3 contiguous legible characters from brand name visible on physical object
     * Text on: product packaging, device body, booth signage, branded materials
     * NOT heavily blurred, NOT stylized beyond recognition
     * NOT inferred from color blocks or partial shapes alone

  B. Textual Evidence (Caption/Comments):
     * Brand/product names in Georgian (ტერეა, აიქოსი) or English (TEREA, IQOS, glo)
     * Product mentions in context (e.g., "switched to IQOS", "ახალი ტერეა")
     * Combined with visual context makes detection more confident
     * Text alone WITHOUT visual confirmation requires high contextual certainty

DETECTION STRATEGY:
  1. Visual brand indicators (text/logo/emblem) = PRIMARY evidence
  2. Textual mentions (caption/comments) = SUPPORTING evidence
  3. Both together = HIGHEST confidence
  4. Text only + strong context = MEDIUM confidence (explain reasoning)
  5. Visual only without clear branding = DO NOT detect
```

**Impact:**
- Clarifies that brand words in captions/comments ARE valid evidence
- Establishes clear hierarchy: visual primary, textual supporting
- Defines "3+ contiguous legible characters" rule for visual text
- Allows text-only detection with medium confidence + reasoning
- Eliminates ambiguity about keyword usage

---

### 3. Georgian Language Context (Lines 246-258)

**Problem:** Vague "if you recognize them" created uncertainty about Georgian term handling.

**Before:**
```
GEORGIAN LANGUAGE CONTEXT:
- Common Georgian words in nicotine context (if you recognize them)
- Transliteration patterns (Georgian script mixed with English)
```

**After:**
```
MULTILINGUAL PROCESSING - GEORGIAN & ENGLISH:
- Process ALL text equally regardless of script (Georgian Mkhedruli, Latin, mixed)
- Recognize brand/product names in both languages:
  * Georgian: აიქოსი (IQOS), ტერეა (TEREA), დელია (DELIA), გლო (glo)
  * English: IQOS, TEREA, DELIA, glo, Neo, Ploom, HEETS
  * Transliteration: "terea", "iqosi", "ayqosi" (common variations)
- Common Georgian nicotine-related terms:
  * სიგარეტი (sigareti) = cigarette
  * მოწევა (mots'eva) = smoking
  * ახალი (akhali) = new
  * შეცვლა (shets'vla) = switch/change
- Cultural context: Georgian social media mixes scripts freely, transliteration is normal
- Brand mentions count as evidence when combined with visual/contextual support
```

**Impact:**
- Explicit Georgian vocabulary provided (not "if recognized")
- Both Georgian script AND transliteration supported
- Clear statement that brand mentions are valid evidence
- Cultural context about mixed-script usage

---

## RATIONALE

### Why These Changes Matter:

#### 1. Multilingual Equity
**Original issue:** "Handle both Georgian and English naturally" created ambiguity. Models often default to English when uncertain.

**Improvement:** Explicit instruction to "process ALL languages equally" with no preference removes bias. Transliteration support acknowledges real-world usage patterns in Georgian social media.

#### 2. Evidence Hierarchy
**Original issue:** "No keyword matching" was interpreted too strictly, causing models to ignore brand mentions in captions/comments even when contextually relevant.

**Improvement:** Clear hierarchy:
- PRIMARY: Visual brand indicators (text on physical objects, logos, emblems)
- SUPPORTING: Textual mentions (captions, comments)
- BEST: Both combined

This allows legitimate use of textual evidence without reintroducing blind keyword matching.

#### 3. Brand Text Detection Standards
**Original issue:** "Brand text visible" lacked specificity - how much? how clear?

**Improvement:**
- **3+ contiguous legible characters** = quantifiable threshold
- **NOT heavily blurred/stylized** = quality requirement
- **Physical object only** = prevents confusion with unrelated text

Examples that NOW pass:
- "TER" visible on TEREA pack edge = YES (3+ chars)
- "IQO" on device body = YES (3+ chars)
- Turquoise color alone = NO (no text)
- "I" partially visible = NO (<3 chars)

#### 4. Text-Only Detection Path
**New addition:** Allows detection based on strong textual evidence + context:
- Caption: "ახალი ტერეა გემოვნება" (new TEREA flavor)
- Visual: Hand holding something cylindrical (not clearly branded)
- Comments: Multiple mentions of "TEREA"
- **Result:** MEDIUM confidence detection with reasoning explained

This handles real-world cases where:
- Product is partially obscured
- Image quality is low
- Brand is mentioned explicitly in text

---

## VALIDATION

### Test Cases:

#### Case 1: Pure Visual (High Confidence)
- Image: TEREA pack with "TEREA" visible (5+ chars clear)
- Caption: "🔥" (no text)
- **Detection:** YES - visual evidence sufficient

#### Case 2: Visual + Text (Highest Confidence)
- Image: Hand with slim object (brand unclear)
- Caption: "Switched to IQOS TEREA"
- **Detection:** YES - textual evidence confirms ambiguous visual

#### Case 3: Text Only (Medium Confidence)
- Image: Person at table, no clear product
- Caption: "ახალი აიქოსი ილუმა" (new IQOS ILUMA)
- Comments: "როგორაა?" (how is it?)
- **Detection:** POSSIBLE - medium confidence, requires reasoning

#### Case 4: Insufficient Evidence
- Image: Turquoise color scheme, no text
- Caption: "🔥💯" (emojis only)
- **Detection:** NO - color alone insufficient

---

## BACKWARDS COMPATIBILITY

**Concern:** Will existing good detections break?

**Analysis:**
- ✅ Previous visual detections: STILL VALID (rules unchanged)
- ✅ Ultra-strict false positive prevention: MAINTAINED
- ✅ Emoji rules: UNCHANGED
- ✅ Shape confusion prevention: UNCHANGED
- ✅ Hand-near-face rules: UNCHANGED

**New capability:** Legitimate brand mentions in text can now contribute to detection instead of being ignored.

---

## EXPECTED IMPACT

### On Detection Rate:
- **Previous:** 0% in Run #3 (50 posts) - ultra-strict worked
- **After refinement:** Expect 0-5% detection rate
- **Increase from:** Capturing legitimate mentions that were previously missed
- **No increase in:** False positives (same strict rules apply)

### On Success Rate:
- **Current:** 70% (7/10) after restart, 3 failed
- **Expected:** Should remain similar or improve
- **Reasoning:** Clearer instructions reduce model confusion

### On Multilingual Handling:
- **Before:** Possible English bias in edge cases
- **After:** Equal treatment of Georgian/English/mixed text
- **Result:** Better cultural accuracy for Georgian market analysis

---

## WHEN APPLIED

**Status:** Applied during active analysis
- **Posts analyzed before changes:** 0-13 (old prompts)
- **Posts after changes:** 14+ (refined prompts)

**Note:** Analysis is currently running (post 13+). New rules apply to all subsequent posts.

---

## MONITORING

**Watch for:**
1. Detection rate staying within 0-10% range
2. False positive rate remaining at 0%
3. Georgian text being properly recognized
4. Text-based detections having clear reasoning

**Success criteria:**
- ✅ No false positives from color/shape alone
- ✅ Georgian brand mentions recognized
- ✅ Text+visual combined detections work
- ✅ Success rate >90%

---

## FILES MODIFIED

- **src/prompts.py** (Lines 16-21, 43-83, 246-258)

**Backup:** Git tracks all changes, can revert if needed

---

**Refinement Status:** ✅ COMPLETE
**Analysis Impact:** Will apply to posts 14+ onwards
**Testing:** Monitor next checkpoint (post 20) for validation

---

**Excellent analysis by user - these refinements address real ambiguities in the original prompt!**
