## Title of project: 

Vizario: AI-Powered Meeting Intelligence Platform for Enhanced Organizational Productivity

### Value Proposition:

Organizations like the United Nations, multinational corporations, and government agencies conduct thousands of meetings annually that are recorded but rarely analyzed effectively. The current status quo involves manual note-taking during meetings, labor-intensive review of recordings, or reliance on basic transcription services that fail to capture contextual information, non-verbal cues, and the relationships between speakers.

Vizario addresses these inefficiencies by integrating into existing video conferencing and storage infrastructure to provide:

1. Comprehensive meeting summarization with key points, action items, and decision tracking
2. Contextual search and retrieval across meeting archives
3. Question-answering capability about meeting content
4. Multi-modal understanding of both verbal and non-verbal communication

The business value proposition centers on:
- **Time Efficiency**: Reducing the average 5-8 hours per week professionals spend searching for information in meeting recordings to minutes1
- **Knowledge Retention**: Preventing critical information loss that occurs when meetings aren't properly documented
- **Institutional Memory**: Creating searchable archives of organizational knowledge contained in meetings
- **Accessibility**: Making meeting content more accessible to those who couldn't attend or need to reference specific information
    
Key business metrics include:
- 70% reduction in time spent searching for information within meeting recordings
- 85% increase in meeting information accessibility and retrieval
- 40% improvement in follow-through on action items identified in meetings
- 50% decrease in redundant meetings due to improved knowledge sharing

### Contributors

| Name             | Responsible for                                                                         | Link to their commits in this repo |
| ---------------- | --------------------------------------------------------------------------------------- | ---------------------------------- |
| All team members | - Verify iff the service outputs correct results. Report to each other if error occurs. Provide feedbacks to each member's git commits and handle pull requests. |                                    |
| Dae Sung, Jin    | Data Pipeline                                                                          |                                    |
| Yongjae, Chung   | Model Serving and Monitoring                                                            |                                    |
| Yunho, Jung      | Training                                                                                |                                    |
| Sehyun, Kim      | Continous pipeline                                                                |                                    |


### System diagram

The system architecture should illustrate:

1. **Data Ingestion Layer**: Video input processing components, including preprocessing and feature extraction pipelines
2. **Model Layer**: Multiple AI models working together (speech-to-text, video frame analysis, multimodal integration)
3. **Storage Layer**: Various databases for different data types (raw videos, processed features, model outputs)
4. **Serving Layer**: API endpoints, caching mechanisms, and load balancers
5. **Monitoring Layer**: Experiment tracking, performance monitoring, and feedback collection systems
6. **Deployment Pipeline**: CI/CD infrastructure showing the flow from development to production
7. **Infrastructure Layer**: Cloud resources including VMs, GPU nodes, and persistent storage



|Resource|How it was created|Conditions of use|
|---|---|---|
|UN Web TV Dataset|Official recordings of UN meetings and events, professionally produced and archived by the United Nations. Available through the UN Web TV platform.|Publicly available for viewing; scraping and usage for research purposes generally permitted with attribution. No explicit license for model training, but falls under fair use for research.|
|YouTube API & Public Meeting Videos|User-uploaded content on Google's YouTube platform. Includes corporate presentations, academic lectures, and government hearings.|YouTube API has usage quotas and requires API key. Content usage governed by YouTube's Terms of Service. Some videos may be licensed under Creative Commons.|
|OpenAI Whisper|Developed by OpenAI, trained on 680,000 hours of multilingual and multitask supervision collected from the web.|Released under MIT license, permitting commercial and research use with attribution.|
|LanceDB|Open-source vector database built for AI applications by developers.|Apache 2.0 license, permitting commercial use, modification, and distribution.|
|VideoDB|Specialized database for video storage and retrieval, optimized for AI applications.|Commercial product with tiered pricing, offering free tier for development with limitations.|
|CLIP (Contrastive Language-Image Pre-training)|Developed by OpenAI, trained on 400 million image-text pairs collected from the internet.|Released under MIT license, allowing commercial and research use with attribution.|
|Hugging Face Video Models|Community-contributed models for video understanding, trained on various public datasets.|Most models available under open-source licenses (MIT, Apache 2.0). Specific license depends on each model.|

### Summary of infrastructure requirements

| Requirement                  | How many/when                         | Justification                                                                                                                                          |
| ---------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Medium CPU VMs               | 5 for entire project duration         | Required for continuous running of the orchestration layer, API servers, databases, and monitoring systems.                                            |
| High-memory VMs              | 2 for entire project duration         | Needed for data preprocessing, feature extraction, and database operations that require significant memory.                                            |
| Large GPUs (16-32GB VRAM)    | 2 for continuous deployment           | Required for inference serving of multiple models simultaneously with low latency requirements.                                                        |
| Very Large GPUs (32GB+ VRAM) | 4 for 8-hour blocks, 2-3 times weekly | Needed for distributed training of large multimodal models. Higher memory GPUs reduce the complexity of distributed training implementation.           |
| Persistent Storage           | 2TB                                   | Required for storing raw video data, preprocessed features, model checkpoints, and experiment artifacts. Video data is particularly storage-intensive. |
| Floating IPs                 | 3 for entire project duration         | Needed for stable endpoints for API service, monitoring dashboards, and experiment tracking server.                                                    |
| Network Bandwidth            | High-throughput connection            | Video data transfer between storage and compute resources requires significant bandwidth.                                                              |

### Model training and training platforms

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
    

### Model serving and monitoring platforms

**Strategy**: Our serving infrastructure will implement a microservice architecture with:

1. **Video Processing Service**: Handles video ingestion, frame extraction, and feature computation.
    
2. **Inference Service**: Provides low-latency model inference for interactive queries.
    
3. **Results Cache**: Stores common queries and preprocessing results to improve response time.
    
4. **API Gateway**: Manages authentication, request routing, and load balancing.
    

**Performance Requirements**:

- Latency: < 2 seconds for question answering on processed meetings
    
- Throughput: Support for 50+ concurrent users
    
- Batch processing: Complete full analysis of 1-hour meeting in < 5 minutes
    

**Model Optimizations**:

- Quantization of vision models to INT8 precision
    
- Knowledge distillation to create smaller, faster models for common query types
    
- ONNX Runtime for optimized inference on CPU and GPU
    
- TensorRT optimization for GPU inference workloads
    

**System Optimizations**:

- Dynamic batching of requests to maximize throughput
    
- Caching of video features and common query results
    
- GPU sharing among multiple inference services with proper memory management
    
- Load balancing across multiple inference endpoints
    

**Monitoring and Evaluation**:

- Implement comprehensive logging of inference requests, timing, and resource utilization
    
- Deploy separate monitoring for data drift, especially for domain-specific terminology
    
- Track user feedback and satisfaction metrics through explicit ratings and implicit signals
    
- Conduct regular A/B testing of model versions in the canary environment
    

**Feedback Loop**:

- Capture user corrections and clarifications as training signals
    
- Implement active learning to identify high-value samples for human annotation
    
- Store production queries and results for periodic re-training and evaluation
    

**Difficulty Point**:

- **Develop multiple options for serving**: We will implement and compare three deployment options: (1) GPU-optimized serving with TensorRT, (2) CPU-optimized serving with ONNX Runtime and quantization, and (3) hybrid approach with model splitting across CPU/GPU based on computational requirements.
    

### Data pipeline

**Strategy**: Our data pipeline will handle two primary workflows:

1. **Offline Training Data**: Collection, processing, and storage of labeled meeting videos
    
2. **Online Inference Data**: Real-time processing of meeting videos and user queries
    

**Offline Data Processing**:

- Implement persistent storage for video data, extracted features, and training artifacts
    
- Develop ETL pipelines for ingesting meeting videos from various sources (UN Web TV, YouTube API, direct uploads)
    
- Create preprocessing workflows for video frame extraction, audio separation, and transcription generation
    
- Store processed features in vector databases (LanceDB) optimized for retrieval
    

**Online Data Processing**:

- Implement streaming pipeline for real-time meeting analysis
    
- Create feature extraction services that process video segments as they become available
    
- Develop query understanding and routing components to direct user questions to appropriate models
    

**Data Management**:

- Use VideoDB for efficient storage and retrieval of video segments
    
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
        

### Continuous X

**Strategy**: Our CI/CD approach will implement GitOps principles with:

1. **Infrastructure as Code**: All infrastructure defined in Terraform and stored in Git
    
2. **Containerization**: Docker containers for all services with Kubernetes for orchestration
    
3. **Continuous Integration**: Automated testing of code, models, and integrations
    
4. **Continuous Deployment**: Automated promotion through staging, canary, and production environments
    
5. **Continuous Training**: Scheduled and trigger-based model retraining
    

**Implementation**:

- Use ArgoCD for GitOps-based deployment of Kubernetes resources
    
- Implement Argo Workflows for orchestrating complex training and evaluation pipelines
    
- Develop Helm charts for all services to standardize deployment across environments
    
- Create GitHub Actions workflows for CI/CD automation
    

**Deployment Environments**:

- **Development**: Individual developer environments for rapid iteration
    
- **Staging**: Integration environment for system testing
    
- **Canary**: Limited production deployment for real-world testing
    
- **Production**: Full deployment for all users
    

**Promotion Process**:

- Staging to Canary: Automated based on passing all offline evaluations and load tests
    
- Canary to Production: Semi-automated with approval gate after monitoring key metrics for 24-48 hours
    

**Continuous Training Triggers**:

- Scheduled retraining on fixed intervals (weekly)
    
- Event-based retraining when data drift exceeds thresholds
    
- Manual triggers for emergency updates or special cases
    

**Immutable Infrastructure Approach**:

- No direct modifications to running infrastructure
    
- All changes made through Git-based workflow
    
- Blue/green deployment strategy for zero-downtime updates
    

**Difficulty Point**:

- **Monitor for model degradation**: We will implement comprehensive monitoring that tracks model output quality through user feedback, automatically detects degradation patterns, and triggers retraining with newly labeled production data when quality drops below thresholds.
    

This implementation of continuous processes ensures that our entire MLOps lifecycle is automated, traceable, and resilient to failures.