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



### Model Serving

**Serving from an API endpoint**: You must wrap your model in an API endpoint for serving. (If you implement a front end, it will call your API.)

- We will serve our model output through an API endpoint using Fast API. Our frontend will be a Gradio Python Client, that connects to this API endpoint.
- https://www.gradio.app/guides/fastapi-app-with-the-gradio-client

**Our Performance Requirements**:

Our current goal is to achieve these following metrics for production.

- Latency: < 2 seconds for question answering on processed meetings
- Throughput: Support for 50+ concurrent users
- Batch processing: Complete full analysis of 1-hour meeting in < 5 minutes

**Model optimizations to satisfy requirements**:

- Quantization of vision models to INT8 precision
- Knowledge distillation to create smaller, faster models for common query types
- ONNX Runtime for optimized inference on CPU and GPU
- TensorRT optimization for GPU inference workloads

**System optimizations to satisfy requirements**:

- Dynamic batching of requests to maximize throughput
- Caching of video features and common query results
- GPU sharing among multiple inference services with proper memory management
- Load balancing across multiple inference endpoints

---

**Difficulty Point**:

- **Develop multiple options for serving**: We will implement and compare three deployment options: (1) GPU-optimized serving with TensorRT, (2) CPU-optimized serving with ONNX Runtime and quantization, and (3) hybrid approach with model splitting across CPU/GPU based on computational requirements.

---

### Evaluation and Monitoring

**Offline evaluation of model**:

1. Evaluate on “standard chatbot” capability, and “meeting specific” use cases.
2. Evaluate on populations and slices of special relevance
    - Evaluate speaker bias - we will analyze the chatbot's performance based on the speaker's country, gender, or role.
    - We also aim to evaluate the performance on different topics discussed in the meetings (e.g., humanitarian, security, environmental issues, etc).
3. Handling Known failure models
    - We will test the chatbot's ability to handle ambiguous or vague questions, by creating a dataset of ambiguous queries with generative AI, and evaluate the chatbot's responses, through offline testing.
    - We also will verify with Human in the loop, to check if the system might be hallucinating and generating incorrect or made up information.
4. Employing unit tests based on templates:
    - We create a template-based unit testing suite. Some examples:
        - "Who spoke about [topic] on [date]?"
        - "Summarize the discussion on [topic]."
        - "What was the vote count for resolution [number]?"
        - "What country proposed [resolution]?"

The metrics for these tests will include: accuracy, precision, recall, F1-score, BLEU, ROUGE.

All results will be logged to MLflow, for comparing models over time.

**Load test in staging**: 

- Once our CI/CD pipeline deploys the service in a staging environment, load tests will be automatically triggered via GitHub Actions whenever an updated model is staged, ensuring that any performance regressions are promptly identified.

**Online evaluation in canary**:

- After passing staging tests, the service will be deployed in a canary environment for online evaluation.
- We will simulate real-world user behavior by acting as a diverse set of artificial “users” (for instance, diplomats from various countries) to test the system’s responsiveness and reliability.
- In addition to template-based unit tests, we will perform red teaming exercises to challenge the model and confirm it operates as intended.

**Closing the loop**:

- Feedback will be sourced from explicit user ratings (eg. thumbs up/down), and human-in-the -loop analysis of natural ground-truth labels.
- We will save a portion of production data, and label them periodically, for retraining and improving the model.

**Business-specific evaluation:**

We will define and monitor key business metrics stated in the value proposition, such as reductions in search time, improvements in meeting accessibility (we will comparing time spent to manual searching) to measure the model’s impact on organizational productivity.

**Difficulty Points:**

- **Data Drift Monitoring:** After our system is deployed in production, we aim to continuously monitor for data and label drift. We will continue to log each model in MLFlow, and track changes in model behavior that way.
- **Model Degradation Detection:** With human annotators (us), we will observe for performance degradation and employ an automated retraining process with new, labeled, production data through our CI/CD pipeline.