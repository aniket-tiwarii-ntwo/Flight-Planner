# flight-planner-project

## NER Dataset – My Challenges & Fixes (Flight Booking)

| S.No | Problem                  | Why this bites me | What I’ll do about it |
|------|--------------------------|-----------------|----------------------|
| 1    | **SOURCE vs DESTINATION**   | spaCy just calls cities `GPE`, doesn’t tell me if it’s “from” or “to”. | |
| 2    | **AIRLINE vs ORG**          | Airlines (e.g., Singapore Airlines) show up as `ORG` instead of airline. | |
| 3    | **Departure vs Arrival**    | Both are times → model might mix them up. | |
| 4    | **Date formats**            | Dates come in every shape: `2025-09-15`, `15th Sep`, `tomorrow`. | |
| 5    | **Prices & currencies**     | `$500`, `under 40,000 INR`, `less than EUR 200` – messy variety. | |
| 6    | **Time expressions**        | People say “after 6pm”, “between 12–6”, “midnight” etc. | |
| 7    | **Annotation mistakes**     | (“York” instead of “New York”). | |
| 8    | **Pretrained label overlap**| spaCy insists on predicting `ORG/GPE` even when I want custom labels. | |
| 9    | **Ambiguous words**         | word can have many meaning. ( eg - "Buisness - can be Flight class and profession) | |
| 10   | **Missing variables**       | People don’t always mention everything (like no source location). | |
| 11   | **Multi-word locations**    | Names like “Los Angeles” sometimes get split (it may consider Los and Angeles different ) | |
| 12   | **Template rigidity**       | If I only train on fixed templates, model won’t generalize. | |
| 13   | **Casual/short queries**    | Real-world queries are shorthand like “2 ppl biz NY → Tokyo Fri night.” | |
| 14   | **Evaluation issues**       | High accuracy on templates does not mean real-world performance. | |