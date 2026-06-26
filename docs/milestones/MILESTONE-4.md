# MILESTONE 4: MODEL ITERATION AND TUNING

## GOAL

Improve ANDI's generated relationship intelligence by tuning extraction, dossier generation, patching, drafting, source-support review, voice match, reliability, regression testing, and cost performance.

## OWNERSHIP

* **Primary owner:** Soham Kinhikar
* **Supporting owners:** Jayraj Joshi and Bhuvnesh Verma

## SCOPE AND PLANNING

* **Estimated duration:** 2–4 weeks, depending on evaluation volume, writing-sample availability, and model/provider experimentation.
* **Dependencies:** Milestone 2 evaluation harness, representative dossiers, source references, draft samples, cost tracking, prompt tracking process, and enough writing samples to tune the voice profile.
* **Client or user validation required:** Yes. Voice match, dossier usefulness, source-support quality, and relationship sensitivity require human review.

## SCOPE NOTES

Milestone 4 is the quality, reliability, and cost-control phase. The purpose is not simply to "make the model better," but to make each generated output measurable, reviewable, source-grounded, and safe to use. Every prompt change should be treated like a product change: it needs a baseline, a test set, a measured result, and a regression check.

This milestone should preserve the version-one safety boundary: ANDI may draft recommendations, summaries, talking points, and messages, but it should not send outreach automatically. Any user-facing message generated in this milestone must remain in draft or approval-required form.

## DELIVERABLES

* Dossier generation pipeline supporting structured and narrative outputs using approved internal formats.
* Field-level dossier specification covering required fields, optional fields, source-reference rules, missing-evidence behavior, and confidence labels.
* Patch system that can revise generated dossiers, briefs, and drafts for writing style, risk flags, relationship context, accuracy, and talking points without rewriting unrelated sections.
* Draft-generation pipeline using a user-specific voice profile while preserving explicit user approval before sending.
* Source-support review system that checks whether generated claims are supported by source emails, calendar events, LinkedIn-derived records, contact graph records, or user-provided notes.
* Model and prompt iteration log showing baseline metrics, prompt versions, model versions, cost impact, quality impact, and regression results.
* Voice-profile package containing writing samples, extracted style features, prohibited patterns, preferred phrasing, and a documented voice-match rubric.
* Twenty-draft human review set with ratings, comments, failure modes, and final voice-match score.
* Cost-optimization plan identifying which operations stay on premium models, which can move to cheaper hosted models, and which can be tested on open-source models.
* Benchmark report for at least one extraction task on an appropriate open-source model candidate. This benchmark is exploratory and does not commit the product to using that model in production.
* Prompt/token optimization report comparing baseline usage against optimized usage with quality preserved.
* Regression test suite covering extraction quality, source grounding, unsupported-claim rate, draft safety, model cost, and output format validity.

## DETAILED TASK BREAKDOWN

### Task 4.1: Build dossier generation pipeline with structured and AI-assisted output formats

* Define the purpose of a dossier: what decision it helps the user make, what relationship context it summarizes, and what action it should support.
* Define the structured dossier format with explicit fields for contact identity, relationship tier, relationship summary, recent interactions, open loops, potential opportunities, recommended next action, risks, and source references.
* Define the v5 AI-assisted dossier format that can produce a more narrative, strategy-oriented summary while still mapping back to the structured fields.
* Implement structured output validation so every dossier response is machine-checkable before it is shown to a user.
* Implement fallback behavior for missing evidence, including "unknown," "not enough evidence," or "needs user confirmation" rather than fabricated claims.
* Implement contact-level context lookup from Gmail, Calendar, LinkedIn-derived records, retrieval records, contact graph edges, and stored memory.
* Add dossier version metadata, including prompt version, model version, generation timestamp, contact ID, user ID, source IDs, and cost estimate.
* Create at least 10 representative dossier examples across high-touch contacts, weak ties, dormant contacts, recent meetings, and noisy contacts.

### Task 4.2: Define required fields, optional fields, citation requirements, and missing-evidence behavior

* Mark each dossier field as required, optional, derived, or user-confirmed.
* Define which fields require direct source references, such as recent interactions, meeting references, open loops, and specific claims about relationship history.
* Define which fields can be model-inferred but must carry a confidence label, such as relationship warmth or suggested next action.
* Define which fields must never be invented, including employer, title, personal details, commitments, promises, meetings, deadlines, and sensitive relationship information.
* Add a "citation missing" state that blocks or flags any generated claim that cannot be traced to a stored source record.
* Add clear behavior for stale data, including when old interactions should be marked as historical rather than current.
* Document examples of acceptable and unacceptable generated claims.

### Task 4.3: Build patch system for writing style, risk flags, relationship context, and talking points

* Define patch categories: style patch, factual patch, risk patch, talking-point patch, tone patch, and relationship-context patch.
* Implement a patch input format that specifies the target output, target section, requested change, reason for change, and whether source references must be rechecked.
* Ensure patches can update one section without regenerating the full dossier or draft unless the change affects global context.
* Add risk-flag patches for overconfident claims, sensitive personal references, unsupported assumptions, overly sales-oriented language, and missing user approval.
* Add talking-point patches that can convert relationship context into concise meeting prep bullets.
* Add writing-style patches that adjust tone, directness, length, specificity, and formality while preserving facts and source references.
* Log every patch with before/after text, patch type, source reason, prompt version, and model version.
* Add regression checks to make sure patching does not remove source references, change factual meaning, or introduce unsupported claims.

### Task 4.4: Build draft generation with voice profile integration

* Define supported draft types for version one, such as follow-up email, check-in note, intro request, meeting recap, thank-you note, and soft reactivation message.
* Build a voice profile from approved writing samples, including typical sentence length, greeting style, directness, warmth, sign-off style, use of context, and level of formality.
* Separate factual content from style instructions so the voice layer cannot create unsupported facts.
* Add draft constraints requiring the model to avoid overpromising, pressure tactics, sensitive references, and claims not present in the source context.
* Require every generated message to remain a draft and include an explicit approval boundary before sending.
* Add source-grounded context cards beside or inside the draft-generation process so the user can see why the draft was recommended.
* Generate a 20-draft review set across different relationship types and outreach scenarios.
* Store draft metadata, including source contact, source signals, voice-profile version, prompt version, cost, and approval status.

### Task 4.5: Implement model synthesis with source-support review

* Define citation objects for emails, calendar events, LinkedIn-derived records, contact graph edges, and user notes.
* Require generated factual claims to reference one or more source objects where feasible.
* Implement a claim-checking pass that compares generated claims against retrieved source snippets or structured records.
* Classify each checked claim as supported, partially supported, unsupported, stale, or ambiguous.
* Block or flag unsupported claims in dossiers, briefs, and drafts before user review.
* Add source-reference coverage metrics showing what percentage of factual claims have direct support.
* Add unsupported claims-rate tracking by output type: dossier, brief, draft, and talking points.
* Create a manual review workflow for a reviewer to inspect unsupported or ambiguous claims.

### Task 4.6: Improve extraction quality using the Milestone 2 eval harness

* Identify the weakest extraction categories from Milestone 2, such as names, organizations, commitments, dates, follow-up requests, relationship events, or meeting intent.
* Create an error taxonomy for extraction failures: missed entity, wrong entity, wrong date, wrong relationship, duplicate signal, unsupported inference, stale signal, or irrelevant signal.
* Update extraction prompts, data structures, or routing logic based on the error taxonomy.
* Rerun the evaluation harness after each meaningful change and compare against the Milestone 2 baseline.
* Track precision, recall, F1 where applicable, false-positive rate, false-negative rate, and cost per extraction.
* Save evaluation artifacts so regressions can be traced to specific prompt or model changes.

### Task 4.7: Iterate dossier prompts to reduce unsupported claims and improve output structure

* Establish a baseline unsupported-claim rate, structure-validity rate, source-reference-coverage rate, and reviewer usefulness score.
* Create prompt variants targeting one issue at a time, such as shorter context windows, stricter citation rules, better missing-data handling, or improved action recommendations.
* Run each prompt variant against the same evaluation set before selecting a winner.
* Reject prompt variants that improve style but increase unsupported claims or source-support failures.
* Add explicit instruction patterns for uncertainty, missing data, stale data, and weak evidence.
* Compare structured v4 output against AI-assisted v5 output for accuracy, usefulness, and cost.
* Document the final selected prompt and the reason it was selected.

### Task 4.8: Run draft quality iteration with voice-match scoring

* Define the 20-draft evaluation sample across warm contacts, cold contacts, investors, partners, mentors, dormant contacts, and recent meeting follow-ups.
* Score each draft using the documented voice-match rubric.
* Track separate scores for voice accuracy, factual accuracy, usefulness, relationship sensitivity, brevity, clarity, and likelihood of user approval.
* Identify recurring draft problems, such as sounding too formal, too pushy, too generic, too verbose, or too disconnected from context.
* Modify voice prompts and examples based on the review results.
* Rerun the 20-draft review after major voice-profile changes.
* Maintain a rejected-pattern list so the system avoids phrases or behaviors the user dislikes.

### Task 4.9: Tune voice profile with additional writing samples

* Collect approved writing samples from emails, text-style messages, professional notes, and prior drafts.
* Separate samples by context, such as formal client communication, casual professional follow-up, investor communication, and internal team communication.
* Extract reusable style features, including greeting patterns, sentence length, directness, level of warmth, use of humor, and typical sign-offs.
* Define prohibited style patterns, including language that sounds too corporate, overly apologetic, overly aggressive, generic, or fake.
* Create a voice-profile version history so changes can be rolled back.
* Test the voice profile against the 20-draft sample and compare scores before and after tuning.

### Task 4.10: Create and use a voice-match rubric

* Define a 1–10 scoring scale with written descriptions for each score band.
* Score drafts across at least five categories: tone, structure, specificity, relationship sensitivity, and naturalness.
* Add a factuality gate so a draft with unsupported facts cannot receive a passing score even if it sounds like the user.
* Add a safety gate so a draft that pressures, manipulates, or overpromises cannot receive a passing score.
* Require reviewer comments for any score below 7 so prompt changes have actionable feedback.
* Document examples of passing and failing drafts.

### Task 4.11: Document cost optimization plan

* Break total cost into ingestion, retrieval indexing, extraction, scoring, dossier generation, brief generation, draft generation, source-support review, and patching.
* Identify the top three cost drivers using actual token/model call data.
* Classify operations into premium-model required, cheaper-hosted-model eligible, open-source-model candidate, cacheable, or avoidable.
* Define caching rules for repeated context lookup, repeated dossier generation, and unchanged contact histories.
* Define when to use smaller models for extraction or classification and when to escalate to larger models for synthesis.
* Estimate cost per contact, cost per brief, cost per dossier, cost per draft, and projected cost per active user.
* Document cost-quality tradeoffs and recommend the default model routing plan for beta launch.

### Task 4.12: Benchmark at least one extraction task on an open-source model

* Select one extraction task with a clear expected output, such as commitment extraction, date extraction, contact-detail extraction, or follow-up signal extraction.
* Choose at least one open-source model candidate for exploratory benchmarking only.
* Run the same evaluation sample through the current hosted-model baseline and the open-source candidate.
* Compare accuracy, latency, cost, structured output adherence, citation compatibility, and failure modes.
* Record whether the open-source model candidate appears suitable for user-facing use, offline/batch use only, or not acceptable based on the measured sample.
* Document any infrastructure implications, such as hosting cost, GPU need, latency, quantization, or privacy advantages.

### Task 4.13: Optimize prompts to reduce token usage without quality loss

* Establish token-usage baselines for extraction, dossiers, briefs, drafts, source-support review, and patches.
* Remove redundant instructions, repeated context, overly large examples, and unnecessary message history from prompts.
* Replace long natural-language instructions with compact structured data structures where possible.
* Add retrieval limits so only relevant source context is passed into synthesis.
* Add summarization or caching for long contact histories that do not change frequently.
* Compare optimized prompts against the baseline evaluation set.
* Confirm that token reduction does not reduce extraction accuracy, source-reference coverage, voice-match score, or dossier usefulness.

### Task 4.14: Add regression tests for prompt and model changes

* Build a fixed regression dataset of contacts, source snippets, calendar events, expected extractions, expected signal classifications, and expected output constraints.
* Add structured-output-validity tests for dossiers, briefs, drafts, and patch outputs.
* Add factuality tests for citation-supported claims.
* Add draft-safety tests to ensure outputs remain approval-required and do not claim messages were sent.
* Add cost regression tests that flag major token increases.
* Add minimum-quality thresholds so prompt changes cannot be merged if they reduce key metrics below acceptance targets.
* Store test results with prompt version and model version.

## ACCEPTANCE CRITERIA

* **Dossier data structure readiness:** v4 structured dossier and v5 AI-assisted dossier formats are fully documented, implemented, and data-structure-validated. A generated dossier must include contact identity, relationship tier, relationship summary, recent interactions, open loops, opportunities, recommended next action, risks, confidence labels, source IDs, prompt version, model version, generation timestamp, and estimated generation cost.
* **Dossier field completeness:** On the evaluation set, at least 95% of generated dossiers must include all required fields. Any missing required field must be replaced with an explicit "unknown" or "not enough evidence" state rather than fabricated content.
* **Source grounding:** At least 90% of factual claims in dossiers and briefs must be linked to a source object or explicitly marked as an inference. Unsupported factual claims must be flagged before user review.
* **Unsupported claims control:** Dossier unsupported-claim rate must be below 5% on the evaluation set. An unsupported claim is any generated factual claim that is contradicted by the source record, not present in the source record, or presented as certain when the evidence is ambiguous.
* **Extraction improvement:** Extraction accuracy must improve by more than 10% over the Milestone 2 baseline on the same evaluation harness. The comparison must use the same or a clearly documented equivalent test set, and the report must show baseline score, tuned score, sample size, and major error categories.
* **Regression safety:** No accepted prompt or model change may reduce extraction accuracy, source-reference coverage, data structure validity, or draft-safety pass rate below the agreed thresholds. Any accepted tradeoff must be explicitly documented with rationale.
* **Patch correctness:** The patch system must successfully apply style, factual, risk, talking-point, and relationship-context patches to sample outputs without removing required source references, changing unrelated sections, or introducing unsupported facts.
* **Draft generation safety:** All generated outreach must remain in draft or approval-required form. No workflow in this milestone may send email, calendar invites, LinkedIn messages, or other outreach automatically.
* **Draft voice match:** Draft voice match must average at least 7 out of 10 across a 20-draft review set using the documented rubric. No individual draft may pass if it contains unsupported factual claims, unsafe pressure language, or an overpromise.
* **Voice rubric completeness:** The voice rubric must define scoring bands for tone, structure, specificity, relationship sensitivity, naturalness, factuality, and safety. Drafts scoring below 7 must include reviewer notes explaining the failure mode.
* **Cost plan completeness:** The cost-optimization plan must identify actual cost per extraction, dossier, brief, draft, patch, contact, and active user estimate. It must also identify the top three cost drivers and recommend model routing for beta launch.
* **Token usage reduction:** Total token usage for the selected evaluation workflow must be reduced by at least 15% from the Milestone 2 baseline without reducing extraction accuracy, source-reference coverage, dossier usefulness, or voice-match score. A 20% or greater reduction is the stretch target.
* **Open-source model benchmark:** At least one extraction task must be benchmarked on an open-source model candidate against the hosted-model baseline. The report must include accuracy, latency, cost estimate, structured output adherence, failure modes, and a recommendation on whether the model is suitable for user-facing use, batch-only use, or not acceptable for the tested task. This does not imply that ANDI itself is open source.
* **Evaluation artifact retention:** All evaluation outputs, review sheets, prompt versions, model versions, model-usage reports, and benchmark results must be saved in a reproducible location so later regressions can be traced.
* **User review readiness:** The milestone cannot be closed until a human reviewer has inspected representative dossiers, drafts, source references, and risk flags and confirmed that the outputs are useful enough for beta-level use.

## VALIDATION EVIDENCE REQUIRED

* Milestone 2 baseline versus Milestone 4 tuned evaluation report.
* Dossier format documentation for the approved internal outputs.
* At least 10 representative dossiers with source-support results.
* Source-support review report showing supported, partially supported, unsupported, stale, and ambiguous claims.
* 20-draft voice-match review sheet with reviewer comments and final score averages.
* Patch-system test results showing successful patch types and failure cases.
* Prompt and model iteration log with prompt version, model version, date, reason for change, cost impact, quality impact, and regression result.
* Open-source model benchmark report.
* Model-usage report showing baseline usage, optimized usage, percentage reduction, and quality-preservation checks.
* Cost-optimization plan with recommended model routing for beta launch.

## RISK FACTORS

* Model iteration without a cost plan can burn budget quickly. Cost tracking must happen before large-scale prompt experiments.
* Voice match is subjective. The rubric must be defined before ratings are collected, or the 7/10 target will not be meaningful.
* Open-source models may not meet the quality bar for extraction or source-grounded tasks. Benchmark with a realistic sample before using them in any user-facing workflow.
* Over-optimization for one user's writing style can reduce generalizability. Keep user-specific voice behavior separate from reusable system logic.
* Source-support review may increase latency and cost. The team should measure whether verification runs inline, async, or only for high-risk outputs.
* Aggressive model-usage reduction can accidentally remove important relationship context. Optimization must be evaluated against quality, not just cost.

## OUT OF SCOPE

* Fully autonomous sending or outreach execution.
* Controlled beta launch readiness.
* Model fine-tuning unless explicitly approved after benchmarking and cost review.
* Replacing the whole application architecture solely to support a model experiment.
