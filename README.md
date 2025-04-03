## Title of project

Vizario: AI-Powered Meeting Intelligence Platform for Enhanced Organizational Productivity

## Value Proposition

### Customer Description

A customer X is a diplomat working at the United Nations (or it can be country delegates or government agencies). At the UN, thousands of meetings are conducted and recorded annually, but analyzing these meetings manually requires significant human resource and effort. Secretaries like X must take notes during meetings themselves, and transcription services alone fail to capture critical elements. It is necessary to capture contextual information, non-verbal cues, and the relationships between speakers for in-depth, accurate analysis. How can our AI assistant help this customer overcome these challenges?

### Benefits

- Accurate and rapid access to information :
    
    ```
    - Advanced Search: Quickly locate relevant content by keyword, country, or topic.
    - Customized Summaries: Generate country-specific or issue-based summary reports to support prompt decision-making.
    ```
    
- Easy to get statement information by country or presenter
    
    ```
     - Speaker identification :  detecting speakers by separating representatives of each countries even within the same countries.
    ```
    
- Better understanding with prompt and proper translation
    
    ```
     - Multilingual support : Auto-translation and keyword search to eliminate language barriers.
    ```
    

### Vizario vs. Conventional Approach

|Feature|Conventional|Vizario|
|---|---|---|
|Speaker detection|Manual or inaccurate|Automatic detection|
|Multilingual support|Limited or unavailable|Automatic translation|
|Search and Analysis|Unavailable or minimal|Advanced methods|
|Transcription and summary|Available 1~2 days after meeting|Immediately available|

### Business Metrics

Key business metrics that we aim to improve include:

- 70% reduction in time spent searching for information within meeting recordings
- 80% reduction in time spent performing meeting information summarization and analysis for UN diplomats
- 40% improvement in follow-through on action items identified in meetings
- 50% decrease in redundant meetings due to improved knowledge sharing

Privacy and Ethics Concerns:

- Bias and Fairness
    - Ensure the system is not biased against marginalized groups, or amplifies narratives of dominant groups with fairness metrics.
- Misinformation
    - Ensuring the system does not generate made-up information.
- Data Security
    - Ensure the systems generates answers based on trained, publicly available UN meetings data.

Our mitigations will involve human-in-the-loop evaluation to foster fairness to responses. We will manually check a fraction of responses against these concerns, and incorporate a fairness metric (eg. Demographic Parity). We will also incorporate red-teaming to check for biased responses or hallucinations.

### Contributors

| Name             | Responsible for         | Link to their commits in this repo |
| ---------------- | ----------------------- | ---------------------------------- |
| All team members | **<Value Proposition>** |                                    |

- Understand and clarify our target customer. Evaluate our product’s potential benefits and state specific steps to achieve maximum customer benefits.

**<Peer Review and Feedback>**

- Provide constructive feedbacks to each member's task (git commits). Review and discuss git pull requests quickly.

**<Business Specific Evaluation>** Evaluate production service with respect to business metrics. (latency, accuracy, privacy, robustness, etc.) | | | Dae Sung Jin | **<Data Pipeline>**

- Provision persistent storage on Chameleon (or on private cloud service, if needed).
    
- Set up a separate repository for all the offline data and organize it by data type and purpose.
    
- Build and manage streaming data. Set up data processing and cleaning steps. Generate sample real-time data for simulation. | | | Yongjae Chung | **<Model Serving and Monitoring>**
    
- Wrap the models with API in order to serve it in endpoints. Employ both model-level and system-level optimizations to satisfy the infrastructure requirements.
    
- Define an automated offline model evaluation procedure using MLFlow.
    
- Perform online evaluation in canary environment (With a set of users and also real user scenario, behaviors) | | | Yunho Jung | **<Model Training>**
    
- Fine-tune AI models (Whisper, Llava) with selected dataset (mostly UN meeting videos and transcriptions).
    
- Experiment various approaches to increase training velocity. Use multiple GPUs, model optimization strategies, Ray Train to leverage fault tolerance and hyperparameter tuning, etc. | | | Sehyun Kim | **<Continous Pipeline>**
    
- Employ Ansible to automate provisioning and orchestration.
    
- In deployment, manage products into independent microservices via containers and APIs.
    
- Set an automated pipeline for re-training, evaluating and testing triggered by the new data (streaming data).
    
- Manage three different enviroments for deployment and gradually develop it from “staging”, “canary” to “production”. | |