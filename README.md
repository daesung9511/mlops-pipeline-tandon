## Title of project

Vizario: AI-Powered Meeting Intelligence Platform for Enhanced Organizational Productivity

## Value Proposition

### Customer Description

A customer X is a diplomat working at the United Nations (or it can be country delegates or government agencies). At the UN, thousands of meetings are conducted and recorded annually, but analyzing these meetings manually requires significant human resource and effort. Secretaries like X must take notes during meetings themselves, and transcription services alone fail to capture critical elements. It is necessary to capture contextual information, non-verbal cues, and the relationships between speakers for in-depth, accurate analysis. How can our AI assistant help this customer overcome these challenges?

### Benefits

- Accurate and rapid access to information :
    - Advanced Search: Quickly locate relevant content by keyword, country, or topic.
    - Customized Summaries: Generate country-specific or issue-based summary reports to support prompt decision-making.
    
- Easy to get statement information by country or presenter
     - Speaker identification :  detecting speakers by separating representatives of each countries even within the same countries.
    
- Better understanding with prompt and proper translation
     - Multilingual support : Auto-translation and keyword search to eliminate language barriers.
    

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

**Privacy and Ethics Concerns:**

- Bias and Fairness
    - Ensure the system is not biased against marginalized groups, or amplifies narratives of dominant groups with fairness metrics.
- Misinformation
    - Ensuring the system does not generate made-up information.
- Data Security
    - Ensure the systems generates answers based on trained, publicly available UN meetings data.

Our mitigations will involve human-in-the-loop evaluation to foster fairness to responses. We will manually check a fraction of responses against these concerns, and incorporate a fairness metric (eg. Demographic Parity). We will also incorporate red-teaming to check for biased responses or hallucinations.

**Scale Requirements:**

Our project will mainly leverage the YouTube API to train on a large dataset of public UN meeting recordings. Our system employs three specialized models to address diverse aspects of meeting analysis, and it is deployed on the cloud with separate training and inference pipelines involving multiple GPUs, and the production model will be exposed as an API endpoint accessible via a Gradio frontend.

### Contributors

| Name            | Responsible for                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Link to their commits in this repo |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| All team members | **Value Proposition** <br> - Understand and clarify our target customer. <br> - Evaluate our product’s potential benefits and state specific steps to achieve maximum customer benefits. <br><br> **Peer Review and Feedback** <br> - Provide constructive feedback on each member's tasks (git commits). <br> - Review and discuss git pull requests quickly. <br><br> **Business Specific Evaluation** <br> - Evaluate production service with respect to business metrics (latency, accuracy, privacy, robustness, etc.). |        https://github.com/daesung9511/mlops-pipeline-tandon/commits                         |
| Dae Sung Jin    | **Data Pipeline** <br> - Provision persistent storage on Chameleon (or on private cloud service, if needed). <br> - Set up a separate repository for all offline data and organize it by data type and purpose. <br> - Build and manage streaming data. Set up data processing and cleaning steps. Generate sample real-time data for simulation.                                                                                                                      |                 https://github.com/daesung9511/mlops-pipeline-tandon/commits?author=daesung9511                    |
| Yongjae Chung   | **Model Serving and Monitoring** <br> - Wrap the models with an API to serve them at endpoints. <br> - Employ both model-level and system-level optimizations to satisfy infrastructure requirements. <br> - Define an automated offline model evaluation procedure using MLFlow. <br> - Perform online evaluation in a canary environment (with a set of users and real user scenarios).                                                         |    https://github.com/daesung9511/mlops-pipeline-tandon/commits?author=yongjae354                                 |
| Yunho Jung      | **Model Training** <br> - Fine-tune AI models (Whisper, Llava) using selected datasets (mostly UN meeting videos and transcriptions). <br> - Experiment with various approaches to increase training velocity (multiple GPUs, model optimization strategies, Ray Train for fault tolerance and hyperparameter tuning, etc.).                                                                                                                          |            https://github.com/daesung9511/mlops-pipeline-tandon/commits?author=Yunho-Karl-Jung                         |
| Sehyun Kim      | **Continuous Pipeline** <br> - Employ Ansible to automate provisioning and orchestration. <br> - Manage products as independent microservices via containers and APIs. <br> - Set up an automated pipeline for re-training, evaluating, and testing triggered by new streaming data. <br> - Manage three different environments for deployment, gradually developing from “staging” to “canary” to “production”. |        https://github.com/daesung9511/mlops-pipeline-tandon/commits?author=seanshnkim                             |


### System diagram

<img width="1252" alt="Image" src="https://github.com/user-attachments/assets/2fd2544a-bc14-4ab3-b42e-c33fbd1dcb40" />

### Summary of Outside Materials

| Resource | How it was created | Conditions of use |
| --- | --- | --- |
| UN Web TV Dataset | Official recordings of UN meetings and events, professionally produced and archived by the United Nations. Available through the UN Web TV platform. | It is publicly available for viewing. Scraping and usage for educational purposes are permitted with attribution. |
| YouTube API & Public Meeting Videos | User-uploaded content on YouTube platform. It includes corporate presentations, academic lectures, and government hearings. | YouTube API has usage quotas and requires API key. Content usage is governed by YouTube's Terms of Service. Some videos may be licensed under Creative Commons. |
| OpenAI Whisper | Whisper is developed by OpenAI and shows the SoTA performance in speech-to-text recognition task. It was trained on 680,000 hours of multilingual and multitask supervision collected from the web. | It is released under MIT license. (permits commercial and research use with attribution) |
| LanceDB | Open-source vector database built for AI applications by developers. | Apache 2.0 license. Permits commercial use, modification, and distribution. |
| VideoDB | It is a specialized database for video storage and retrieval, optimized for AI applications. | Commercial product with tiered pricing, offering free tier for development with limitations. |

**Data Resources**

1. Youtube
    1. **UN Security Council meeting on the Middle East** 
        1. [https://www.youtube.com/watch?v=PHZ5BJpXoic](https://www.youtube.com/watch?v=PHZ5BJpXoic&t=1s)
        2. https://www.youtube.com/watch?v=Vk1Fs5WEZsE
        3. https://www.youtube.com/watch?v=wfAa1GiNdgM
        4. https://www.youtube.com/watch?v=Q1B5MyXXslM
        5. https://www.youtube.com/watch?v=ayxtmtMcO6M
        6. https://www.youtube.com/watch?v=cvFTDNP2p50
        7. https://www.youtube.com/watch?v=kybHwj8YZqs
        8. https://www.youtube.com/watch?v=2NZVT3kFC6c
        9. https://www.youtube.com/watch?v=RHv92D_ISgM
        10. https://www.youtube.com/watch?v=QNRoyte6Dyw
    2. **UN Security Council on Ukraine**
        1. https://www.youtube.com/watch?v=GjL8610P890
        2. https://www.youtube.com/watch?v=jAKYNwGSfkY
        3. https://www.youtube.com/watch?v=R1dw75mpsfY
        4. https://www.youtube.com/watch?v=qB3Ja3rFo-Y
        5. https://www.youtube.com/watch?v=H2tq1fFzGio
    
2. [**UN Security Council Transcript**](https://digitallibrary.un.org/search?cc=Meeting+Records&ln=en&p=security+counci) 
    1. https://www.youtube.com/watch?v=6U0a36WSirA
        
        https://digitallibrary.un.org/record/4064913?ln=en
        
    2. https://www.youtube.com/watch?v=8DQg5bUmuug
        
        https://digitallibrary.un.org/record/4065707?ln=en&v=pdf
        
    3. https://www.youtube.com/watch?v=i1rs-VHk0-U
        
        [S_PV.9853-EN.pdf](attachment:2731ef33-ad72-4b83-80f4-9afbde77c33b:S_PV.9853-EN.pdf)
        
3. UN General Assembly
    1. https://gadebate.un.org/en

### Summary of infrastructure requirements

- Since the expected model size of LLAVA will be 1B - 10B, the infrastructure requirements would be planned based on its size referring to [this Large Language Model Metrics](https://www.linkedin.com/pulse/infrastructure-requirements-llms-arivukkarasan-raja-j0acc/)

| Requirement | How many/when | Justification |
| --- | --- | --- |
| Medium CPU VMs | 5 for entire project duration | Required for continuous running of the orchestration layer, API servers, databases, and monitoring systems. |
| 16 GB- 64 GB HBM and DDR4 RAM | 1 for batch training
1 for real time inference | Needed for data preprocessing, feature extraction, and database operations that require significant memory and necessary to store the LLM parameters and intermediate data generated during inference. |
| Nvidia A100s | 1 for batch training
1 for real time inference | Required for inference serving of multiple models simultaneously with low latency requirements. |
| Persistent Storage(NVMe or Chameleon Cloud Storage) | 2TB | Required for storing raw video data, preprocessed features, model checkpoints, and experiment artifacts. Video data is particularly storage-intensive. |
| Floating IPs | 2 for entire project duration | Needed for stable endpoints for API service, monitoring dashboards, and experiment tracking server. |
| Network Bandwidth(10GbE) | High-throughput connection | Video data transfer between storage and compute resources requires significant bandwidth. |

**Strategy**: We will implement a multi-model architecture comprising:

1. **Video Frame Analysis Model**: Fine-tuned CLIP or similar vision transformer to extract visual features and identify key visual elements in meetings (speakers, presentations, etc.).
2. **Speech Recognition Model**: Adapted Whisper model for domain-specific speech recognition optimized for meeting terminology.
3. **Multimodal Integration Model**: Custom transformer-based architecture that combines visual and textual features for holistic understanding of meeting content.
4. **Query Understanding Model**: Fine-tuned language model to process user queries about meeting content.

Our training approach will utilize transfer learning from foundation models to reduce training time and data requirements. The multimodal integration model will be our primary focus for custom training and regular re-training based on user feedback.

**Justification**: This multi-model approach is necessary because single models lack the capability to process both visual and textual information with sufficient accuracy for complex meeting understanding. By specializing models for different aspects of the input, we can optimize each for its specific task while maintaining reasonable training requirements.

**Training Implementation**:

- We will host MLFlow on a dedicated VM for experiment tracking, logging model metrics, hyperparameters, and artifacts.
- Ray will manage our distributed training infrastructure, allowing flexible scaling of resources.
- Our training pipeline will implement gradient accumulation and mixed precision training to maximize GPU utilization.
- For the multimodal integration model, we will implement Fully Sharded Data Parallel (FSDP) training across multiple GPUs to handle the memory requirements of large transformer models.

**Difficulty Points**:

1. **Composed of multiple models**: Our system naturally incorporates four interacting models that process different aspects of the input and collaborate to generate outputs.
2. **Use distributed training to increase velocity**: We will implement and benchmark distributed training using various strategies (DDP vs. FSDP) to identify optimal configurations for our models, documenting training time reduction with increasing GPU count.

**Metrics and Targets**:

- Training throughput target: 200+ video frames processed per second during training
- Training time: Complete model retraining in under 4 hours for rapid iteration
- FSDP memory efficiency: Reduce per-GPU memory requirements by at least 60% compared to standard data parallel training

---

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

---

### Data pipeline

**Strategy**: Our data pipeline will handle two primary workflows:

1. **Offline Training Data**: Collection, processing, and storage of labeled meeting videos
2. **Online Inference Data**: Real-time processing of meeting videos and user queries

**Offline Data Processing**:

- Implement persistent storage for video data, extracted features, and training artifacts
- Develop ETL and preprocessing pipelines for ingesting meeting videos from various sources (UN Web TV, YouTube API, direct uploads)
- Create preprocessing workflows for video frame extraction, audio separation, and transcription generation
- Store processed features in vector databases (LanceDB) optimized for retrieval

**Online Data Processing**:

- Implement streaming pipeline for real-time meeting analysis with UN Live video on Youtube
- Use whisper to convert audio to text or the youtube auto-translate function to generate text
- Create feature extraction services that process video segments as they become available
- Develop query understanding and routing components to direct user questions to appropriate models

**Data Management**:

- Use LanceDB for efficient storage and retrieval of video segments
- Implement data versioning to track changes in datasets over time
- Create data quality monitoring to detect anomalies in incoming video characteristics

**Simulated Online Data**:

- Develop a simulation framework that generates synthetic meeting scenarios
- Create realistic query patterns based on analysis of common information needs
- Implement variable load patterns to test system scalability and resilience

**Difficulty Point**:

- **Interactive data dashboard**: We will implement a comprehensive dashboard using Grafana and custom visualizations that allows team members to:
    - Explore data distribution across different meeting types
    - Analyze model performance on different video characteristics
    - Identify potential biases in model outputs
    - Track data quality metrics over time
    - Monitor storage usage and optimization opportunities

---

### Continuous X

To build and maintain CI/CD pipeline approach, four principles and must be followed:

- **Infrastructure-as-Code (IaaC)**: Employ Ansible and Kubernetes to automate provisioning and orchestration of infrastructures.
- **Microservice Architecture**: For faster and easier deployment, all services must be divided into independent small parts (”microservices”). This also makes it easier to deal with faults (thanks to the isolation of services) and maintain the services as the product grows larger. To achieve it, we will containerize every service and create APIs.
- **Automated pipeline from training to serving**: We will set an automated pipeline using Argo Workflows to re-train, evaluate and test models triggered by streaming data. Also we will develop Helm charts for all services to standardize deployment across environments. Lastly, GitHub Actions workflows can be used for version control.
- Staged deployment: Deploying a product in a staging environment is important to identify and resolve potential bugs. It can also save time and costs caused by unnecessary rollbacks and fixing issues. To perform this step, we will set three different environments: “stage”, “canary”, and “production”. For canary environment, 5~10 artificial users and scenario (user behaviors) will be supposed.
