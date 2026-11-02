# PhishSense: Milestone 3 Research Progress

**Student:** Jamie Alexander  
**Program:** Master of Science in Computer Science  
**Institution:** Full Sail University  
**Project:** PhishSense  
**Development Version:** v0.3.0  
**Milestone:** 3  
**Date:** October 31, 2026

## 1. Research Overview

PhishSense is a browser-based phishing-awareness training application designed to help users improve their ability to distinguish phishing emails from legitimate messages.

The research component investigates the potential effectiveness of adaptive phishing-awareness training compared with a non-adaptive training approach.

The application uses simulated email scenarios, classification exercises, educational feedback, and performance measurements to support this research.

The original research proposal established a pre-test/post-test evaluation of an adaptive training system. Following project committee feedback, the proposed research design has been expanded to include a non-adaptive comparison group.

This revision is intended to help distinguish the effects of adaptive training from improvements that may result from repeated practice and immediate feedback.

## 2. Research Progress During Milestone 3

During Milestone 3, development focused on implementing the application's core training workflow and establishing mechanisms needed for future research data collection.

The following components were implemented:

- A simulated corporate inbox representing the fictional Evercrest Group.
- Training sessions containing ten simulated email scenarios.
- Classification of emails as phishing or legitimate.
- Written explanations of classification decisions.
- Confidence ratings using a five-point scale.
- Immediate educational feedback.
- Recording of classification accuracy.
- Recording of response times.
- Storage of scenario difficulty.
- SQLite database integration for training sessions and responses.
- Tracking of completed emails and training progress.

These features establish the foundation for collecting measurable performance data during future research evaluations.

Although the application can record training responses, the adaptive learning algorithm and formal participant evaluation have not yet been implemented.

## 3. Training Scenario Preparation

The prototype uses training scenarios adapted from the publicly available Phishing and Benign Email Dataset hosted on Hugging Face.

**Dataset repository:** Teddyha/phishing_benign_email_dataset

**Dataset source:** https://huggingface.co/datasets/Teddyha/phishing_benign_email_dataset

Selected examples were reviewed and adapted for use within the PhishSense training environment.

The current prototype contains phishing and legitimate scenarios with predefined classifications, difficulty information, and educational explanations.

The scenarios provide initial testing material for validating the application's classification and feedback workflow.

Further refinement is planned to improve realism, workplace relevance, and difficulty consistency before participant evaluation.

## 4. Revised Research Design

### 4.1 Original Research Design

The original research proposal described a quantitative pre-test/post-test evaluation involving approximately 10–15 adult participants.

Participants would complete a pre-test, adaptive training session, and post-test.

The primary outcome would be classification accuracy, with confidence ratings and response times serving as secondary measures.

The original design did not include a separate non-adaptive comparison group.

### 4.2 Proposed Revised Research Design

Following committee feedback, the study design has been revised to propose approximately 30 adult participants divided into two groups:

**Control Group:** Approximately 15 participants receiving non-adaptive phishing-awareness training.

**Experimental Group:** Approximately 15 participants receiving adaptive phishing-awareness training.

Both groups would complete comparable assessments and training activities.

The primary difference between groups would be the use of performance-based difficulty adjustments in the experimental group.

This design is intended to support a more direct evaluation of whether adaptive training provides benefits beyond those associated with a fixed training sequence.

The revised design remains proposed and will require further review before participant recruitment.

## 5. Research Variables and Measurements

The proposed independent variable is the training approach:

- Adaptive phishing-awareness training.
- Non-adaptive phishing-awareness training.

The primary dependent variable is phishing classification accuracy.

Additional performance measures include:

- Confidence ratings.
- Response times.
- Written reasoning.
- Scenario difficulty.
- Changes in performance between pre-test and post-test assessments.

The application currently supports recording several of these measurements during prototype training sessions.

Pre-test and post-test assessment workflows and the experimental group assignment process remain future development tasks.

## 6. Planned Adaptive Learning Method

PhishSense is intended to use predefined performance-based rules rather than machine learning.

The original research proposal specifies three difficulty levels:

- Beginner.
- Intermediate.
- Advanced.

The proposed adaptation rules evaluate performance after every five training scenarios.

- Accuracy of 80% or higher increases difficulty by one level.
- Accuracy below 60% decreases difficulty by one level.
- Accuracy between 60% and 79% maintains the current difficulty.

Difficulty would remain within the three predefined levels.

These rules are documented in the original research proposal but have not yet been implemented in the application.

The rules may be refined during future development and testing.

## 7. Research Status and Limitations

As of Milestone 3, PhishSense has a functional training prototype capable of presenting simulated emails, recording classification decisions, and providing educational feedback.

However, the application is not yet ready for formal participant evaluation.

Outstanding research-related development includes:

- Implementation and testing of adaptive difficulty adjustments.
- Development of the non-adaptive control-group workflow.
- Implementation of pre-test and post-test assessments.
- Refinement and validation of training scenarios.
- Development of performance summaries and research data analysis procedures.
- Review of the revised research methodology.
- Completion of required institutional research approvals before participant recruitment or data collection.

No formal participant data has been collected, and no experimental findings are reported.

## 8. Next Research Steps

The next phase of PhishSense development will focus on implementing the adaptive learning algorithm and establishing the separate experimental and control-group workflows.

Additional work will include refining the training scenarios, implementing assessment functionality, and validating the accuracy of recorded performance measurements.

The revised research design will also need to be reflected in the formal research proposal and reviewed through the appropriate academic approval process.

Once the application and research procedures are ready and all required approvals have been obtained, participant evaluation may begin.

## 9. Research Materials

The following materials document the current research progress:

**Original Research Proposal:** `research/PhishSense_Research_Proposal.docx`

**Milestone 3 Research Update:** `research/Milestone3_Research_Progress.md`

**Approved Prototype Scenarios:** `data/scenarios_approved_for_prototype.jsonl`

**Application Source Code:** `app.py`

**Database Schema:** `schema.sql`

**Scenario Import Script:** `import_scenarios.py`

These materials document the relationship between the proposed research methodology and the current PhishSense implementation.

## 10. Summary

Milestone 3 established the core interactive training workflow required for the PhishSense research project.

The application now supports simulated email classification, written reasoning, confidence ratings, immediate feedback, and performance data recording.

The research design has also evolved from a single-group pre-test/post-test evaluation toward a proposed comparison of adaptive and non-adaptive phishing-awareness training.

Although additional development and research approval are necessary before formal evaluation, the current milestone represents measurable progress toward implementing and evaluating the PhishSense system.