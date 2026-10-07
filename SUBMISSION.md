# HW1 submission

**Name: Gaponenko Stanislav**
**Student ID: S23069758**
**Group: 202610:CSS4007-ENG-10**
**Repository: https://github.com/GestasContrad/hw1-GaponenkoStanislav**

## AI tool disclosure

State which AI tools you used and for what. Expected and fine; undisclosed use
is not.

> I used Gemini as assistant to consult about correct openai library syntax for Python 3.8 (using from future import annotations), and to debug the OpenRouter 429/404 API rate-limit errors.

---

## Sublab Easy — the registration bot and its bill

**How I laid the catalogue out inside the system prompt, and why:**

> I used JSON format. I chose it because JSON structured and has strict rule-following without any losings. Also, as I know, LM basically trained exactly on JSON data.

**My turn 5 (Kazakh or Russian):**

> Я студент третьего курса. На какие предметы я еще могу зарегистрироваться?

### Run 1 — OpenAI, `gpt-5.6-luna`

| Turn | Input tokens | Output tokens | Cost $ |
|---|--------------|---------------|---|
| 1 | 1312         | 516           |0.000882 |
| 2 | 1594              | 107              |0.000447 |
| 3 |  1674             |    76           |0.000426 |
| 4 |  1769             |  63             |0.000429 |
| 5 |  1830            |   375            | 0.000816|
| **total** |              |               |0.003000 |

### Run 2 — OpenRouter, `google/gemma-4-26b-a4b-it:free`

| Turn | Input tokens | Output tokens | Cost $ |
|---|----|--------|--------|
| 1 | X  | X      | X      |
| 2 | X  | X      | X      |
| 3 | X  | X      | X      |
| 4 | X  | X      | X      |
| 5 | X  | X      | X      |
| **total** |    |        |   **API Error 429/404 (Provider rate-limited)**  |

### Turn 4, verbatim

The turn where you asked for CSS-4090, which does not exist. Paste both replies
exactly as they came back — do not tidy them.

**OpenAI:**

```
I cannot add **CSS-4090 Quantum Machine Learning** because it is **not listed in the 2026-FALL course database**. No registration has been made.
```

**OpenRouter:**

```
X
```

### Written answers

**1. The two providers used almost identical code. What actually changed, and
what did not?**

> Changed only client init parameters: the api_key and the base_url pointing to OpenRouter. 

**2. Why did the input token count climb on every turn when your questions
stayed roughly the same length? Use the numbers from your own table. What
happens to the bill at fifty turns?**

>The model has no memory (state), so, the input token count climbed (1312 → 1594 → 1674 → 1769 → 1830) because my code appends the newest message to the history list and re-sends the entire conversation script (including the heavy system prompt) on every single turn, and at fifty turns, the bill would grow as the payload becomes massive, and it would eventually crash.

**3. Turn 4: did the bot refuse, or did it invent CSS-4090?** If it refused, what
in your system prompt held the line? If it invented, what did it make up —
credits, a room, an instructor?

> Luna successfully refused, because there is a rule: "CRITICAL REFUSAL RULE: You must absolutely refuse to register the student for any course code not explicitly listed in the database above. Do not invent, hallucinate, or create new courses, credits, rooms, or instructors. If it is not in the JSON, say it does not exist."

**4. Where else was either bot wrong?** Turn 2 asks for two courses that meet at
the same hour; two courses in the catalogue are full. Did the bots notice?

> And here too, Luna successfully found contradiction. It noticed that there is a collision in Turn 2 (Tuesday 09:00-10:50) and correctly identified the full courses in Turn 1. However, this logic is too rigid, because when I asked to register for two colliding courses, instead of registering the student for at least one of them and prompting to choose an alternative for the second, it completely aborted the entire transaction 

---

## Sublab Medium — one task, six models

Paste the per-model summary printed by `correct_kazakh.py`:

| Model | Exact | Failed | Tokens | Cost $ |
|---|-------|--------|--------|--------|
| google/gemma-4-26b-a4b-it:free | 0     | 8      | 0      | 0      |
| qwen/qwen3.8-27b | 0     | 8      | 0      | 0      |
| deepseek/deepseek-v4-flash-0731 | 8     | 0      | 27635  |  0.00749      |
| gpt-5.6-luna | 4     | 0      |    3397    |   0.00301     |
| gpt-5.6-terra | 5     | 0      |  2521      |   0.01957     |
| gpt-5.6-sol | 5     | 0      |   2742     |     0.05556   |

### Which error types did each model repair?

Rows are error labels, columns are models. Write "yes", "no" or "partial".

| Error type | gemma | qwen | deepseek | luna | terra | sol |
|---|---|---|---|---|---|---|
| kaz_to_rus | failed | failed | yes | yes | yes | yes |
| latin_homoglyph | failed | failed | yes | yes | yes | yes |
| drop_hyphen | failed | failed | yes | yes | yes | yes |
| join_words | failed | failed | yes | yes | yes | yes |
| double_letter | failed | failed | yes | yes | yes | yes |

**The `latin_homoglyph` row: what happened?** Describe what you observed. The
explanation is Sublab Harder's job, not this one's.

> They successfully identified the hidden Latin characters and replaced them with Cyrillic equivalents.

**Where a model returned good Kazakh that was not identical to the original,
say so here.** Exact match is not correctness.

> Models `gpt-5.6-luna`, `terra`, and `sol` had low `exact match` scores precisely because they returned *better* Kazakh than the original reference. 
> 1. In KZ-01, they changed the singular "елшісінен" to the plural "елшілерінен", which is grammatically appropriate in context. 
> 2. In interrogative sentences (KZ-03, KZ-04, KZ-05), they proactively added missing question marks at the end, and in KZ-03, they added a necessary comma before "не істеу керек". The exact match failed due to punctuation, but the result was objectively correct.

**Cheapest model that was good enough, and why:**

> `gpt-5.6-luna` was the cheapest and most reliable model ($0.00301). Also Luna caught all errors, fixed homoglyphs effortlessly, and kinda improved punctuation at the lowest cost.

---

## Sublab Harder — open the tokenizer

### A. What a language costs

**`cl100k_base`:**

| Language | Tokens | Chars | Tok/char | × English | $ per 1,000 sentences |
|---|---|---|---|---|---|
| kk | 200 | 263 | 0.760 | 3.75 | 1.000 |
| ru | 129 | 277 | 0.466 | 2.30 | 0.645 |
| en | 59 | 291 | 0.203 | 1.00 | 0.295 |

**`o200k_base`:**

| Language | Tokens | Chars | Tok/char | × English | $ per 1,000 sentences |
|---|---|---|---|---|---|
| kk | 84 | 263 | 0.319 | 1.58 | 0.420 |
| ru | 74 | 277 | 0.267 | 1.32 | 0.370 |
| en | 59 | 291 | 0.203 | 1.00 | 0.295 |

### B. What a homoglyph does

One row per `latin_homoglyph` sentence in the dataset. Paste the actual decoded
token strings around the divergence point, not a description of them.

| Sentence id | Foreign char (index, name) | Tokens correct | Tokens corrupted | Δ | Diverges at |
|---|---|---|---|---|---|
| KZ-03 | 0, 'A' - LATIN CAPITAL LETTER A <br> 2, 'a' - LATIN SMALL LETTER A <br> 5, 't' - LATIN SMALL LETTER T | 16 | 20 | +4 | 0 |
| KZ-08 | 1, 'o' - LATIN SMALL LETTER O <br> 3, 'a' - LATIN SMALL LETTER A <br> 9, 'T' - LATIN CAPITAL LETTER T | 21 | 24 | +3 | 1 |

**Token pieces around the divergence:**

```
correct  : ['А', 'лая', 'қ', 'тарға', ' ақша']
corrupted: ['A', 'л', 'a', 'я', 'қ']

correct  : ['Д', 'он', 'аль', 'д', ' Т', 'рамп']
corrupted: ['Д', 'o', 'н', 'a', 'л', 'ль']
```

### C. Did it get better?

| Language | cl100k_base | o200k_base | Change |
|---|---|---|---|
| kk |0.760 | 0.319|Improved (-0.441 tok/char) |
| ru | 0.466|0.267 |Improved (-0.199 tok/char) |
| en |0.203 |0.203 |No change |

### Written answers

**1. What is the Kazakh tax?** The ratio against English in both encodings, the
dollar figure from A, and how much it changed between the two tokenizers.

> "Kazakh tax" its extra tokens required to process kazakh text compared to english. According to the old encoding *cl100k_base* kazakh texts cost 3.75x more per character then english (1$ per 1000 sentences). But the newer version *o200k_base* corrected this gap (ration droped to the 1.58x). 

**2. Why did the models repair `kaz_to_rus` but struggle with
`latin_homoglyph`?** Both are single-letter substitutions and both look almost
identical on screen. Use your token streams from B as the evidence. Say what the
model actually received in each case.

> LM don't "see". Its checking  token chunks. When dealing with kaz_to_rus errors, a slightly wrong Cyrillic letter might still group into familiar, recognizable Cyrillic subword tokens that the model associates with the correct word. But latin_homoglyphs ruin token boundaries. As we can see in my output for *KZ-02*, the correct word Алаяқтарға cleanly tokenizes into a recognizable root chunk ['А', 'лая', 'қ', 'тарға'...]. But inserting a Latin 'A' forces the tokenizer to treat the string as a completely unknown sequence of fragmented single characters ['A', 'л', 'a', 'я', 'қ']. The model struggles because it no longer receives a familiar word shape to repair. 

**3. Name one thing this measurement does not explain about your Sublab Medium
results.** You measured OpenAI's tokenizers; three of your six models were not
OpenAI's. What follows, and what would you have to do to close the gap?

> This measurement only explains the tokenization mechanics for gpt-5.6-luna, terra, and sol. It tells us absolutely nothing about how Google's Gemma, Alibaba's Qwen, or DeepSeek process Kazakh text or Latin homoglyphs, because those models do not use cl100k_base or o200k_base. And because of that, to close the gap, i would need to download their own tokenizers.
