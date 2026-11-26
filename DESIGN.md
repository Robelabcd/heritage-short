# Design

Written before anything was generated.

## Audience
Students who are about to leave home, or have just left, to study abroad. They watch
on their phones, mostly in vertical feeds (TikTok, Instagram Reels, YouTube Shorts)
and in WhatsApp groups, so the 9:16 cut is the main version.

## Intent
When the film ends, viewers should feel that the loneliness of the first months
abroad is normal and passes, and take away one thing they can do about it: rebuild
the habits that kept them connected at home, and share them with new people.

## Story
**Logline:** A student from Addis Ababa learns that the coffee ceremony he left behind
was never about the coffee: it was about not carrying things alone.

**Structure:** three acts, matching the three rounds of an Ethiopian coffee ceremony.

| Act | Round | Story | Colour |
|---|---|---|---|
| 1 | Abol (first round) | Home in Addis: coffee, people, deep conversations about life | Warm amber |
| 2 | Tona (second round) | Maryland: kind but busy people; stress carried alone | Cool blue-grey |
| 3 | Baraka (blessing) | He brews coffee for new friends and shares the weight again | Warm again |

**Motif:** the coffee ceremony, seen three times, meaning more each time.

**Key line:** my mother on the phone, in Amharic: ለሰው መድኃኒቱ ሰው ነው
("The medicine for a person is a person.")

## Design choices
- One character must stay consistent (me). Family appears from behind, as hands, or
  out of focus, which keeps identity drift low and respects their privacy.
- The colour arc carries the story with the sound off, as many people watch in muted feeds.
- English narration reaches students from any country. The one Amharic line keeps the
  film's heritage and is subtitled in English.

## User test 1: radio cut

**How:** 25 Nov 2026. The radio cut (narration, subtitles and a placeholder chord over a black screen, 83 s) was sent on WhatsApp to three people with five open questions. Replies are paraphrased by me from their messages, with the meaning kept. The originals are kept privately.

**Testers:**
- T1: Ethiopian MS student in the US
- T2: high school student in Ethiopia
- T3: Ethiopian BTech graduate, now working (knows the ceremony well)

| Question | T1 | T2 | T3 |
|---|---|---|---|
| What was it about? | A student abroad who misses home and realises what the coffee ceremony means to them | Leaving Addis and looking back on the everyday moments that brought people together | A student far from home discovering the comfort and connection of the coffee ceremony |
| What stayed with you? | The Amharic proverb in the mother's voice, about valuing other people | The ceremony giving everyone a chance to sit together and talk about their day | That gathering over coffee and sharing your day can help people heal |
| Confused or bored? | No | No | No |
| Narration | Easy to follow, natural pace | Comfortable, enough time to take it in | Easy to follow, not rushed or slow |
| Change one thing | Add a specific memory from home | More about life abroad and how it feels different | Make one memory more vivid so we can picture it |

**What we learned:**
- 3/3 told the theme back in their own words, so the story lands without pictures.
- The peak works: what stayed with them was the proverb, and the idea that sharing your day heals.
- The pace is right at 1.7 words per second, so shot durations stay as they are.
- 3/3 asked for more specific detail: two about a memory from home, one about life abroad.

**What changed:** the s03 narration went from "And between them, we talk about everything." to "Incense, gossip, and my mother's TV drama.": three real details from my family's ceremonies (a smell, a sound, a picture) in place of a general phrase. This re-ran one TTS call and the edit, with no image or video calls (see runs.jsonl). The first wording, "Between them: incense, gossip, and my mother's TV drama.", ran 1.0 s past the shot. `make assemble` warned, so I cut two words (one more TTS call).

**Not changed yet:** more about life abroad (T2). Act 2 already spends two shots on it (s05, s06). Adding a shot would lengthen the film and blur which change caused what, so test 2 checks whether the request still stands.

## User test 2: near-final cut

**How:** 26 Nov 2026. The near-final film (9:16, with the three Wan clips) was sent on Snapchat to three new people with six open questions, to watch once on their phones. Their replies are summarised below, with short quotes in their own words; the originals are kept privately.

**Testers:**
- T4: Ethiopian BTech graduate who studied abroad, now working
- T5: Ethiopian BTech graduate who studied abroad
- T6: tech employee living in Saudi Arabia

| Question | T4 | T5 | T6 |
|---|---|---|---|
| What was it about? | "finding something to reunite you with people, in this case, coffee" | The memory of home, and sharing your culture to bring people together | "The company of the people is what makes everything more beautiful" |
| What stayed with you? | The five friends drinking coffee, and the last line | The phone call with the mother | The proverb |
| Confused or bored? | No | Not bored (see the next row) | No |
| Narration and music | Heard clearly | "The volume was perfect" | Clear; the music did not get in the way |
| Anything strange or AI-ish? | The green coffee beans; "maybe use semi-roasted" | The jebena "doesn't look like jebena"; the family's clothes look Arab, one woman in a hijab; the roasting hands look like a man's, the stirring stick floats, a hand is on the hot pan; "green beans" should be "coffee beans" | Nothing |
| Change one thing | The green coffee beans | Make the setting and clothes more accurate | Nothing; would like to join a coffee ceremony |

**What we learned:**
- 3/3 told the story back in their own words, and the peak works: the call with my mother and the proverb.
- Sound is solved: all three heard the narration clearly.
- Every problem was cultural accuracy, and it came from the tester who knows the ceremony best. The models got the style right and Ethiopian specifics wrong, and only someone from the culture could see it.

**What changed:**

| Feedback | Change | Calls |
|---|---|---|
| s02: a man's hands, a floating stick, a hand on the hot pan (T5); green beans look strange (T4) | A mother's hands in a habesha kemis, the stick held in one hand, the other hand away from the pan, beans turning brown | 1 image |
| s03: clothes look Arab (T5) | Habesha kemis with tibeb borders and netela shawls. s03 goes back to a still with a slow camera move, because its Wan clip showed the old clothes | 2 images |
| The jebena looks like a teapot (T5) | A new jebena description from a reference photo, used as words only, then three rounds of reference images (E11). The four jebena shots regenerated | 12 + 4 images |
| "Green beans" sounds like the vegetable (T5) | s08 narration: "raw coffee beans", made live in the walkthrough | 1 TTS |

**Not changed:** the s09 Wan clip still shows the old jebena; re-rendering it is about 21 GPU minutes. One woman in the background of s03 still wears a headscarf. The overall AI look (T5) is the illustration style, so it stays.
