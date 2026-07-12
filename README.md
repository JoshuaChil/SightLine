# SightLine
Intel Global AI Award 2025. Matches Apple Depth Pro metric depth maps to YOLOv8 object detections to provide spatially aware system prompts powering an AI blind-navigation LLM. Connected to ESP32S3 smart glasses for real-time use via smart glasses.

## Project Submission Video

[![Sightline Submission Video](https://img.youtube.com/vi/PD6jf_h__8Q/0.jpg)](https://www.youtube.com/watch?v=PD6jf_h__8Q)

## Picture of Wearable

![Picture of the glasses](/glasses.jpeg)

## Project Synopsis

Over 43 million people globally were estimated to be completely blind, a condition
disproportionately impacting low/middle income countries (Pseudovs, 2024).
Sightline is our solution to reduce these inequalities (UN SDG #10): AI glasses that enable 
hands-free environmental awareness through voice interaction. The system uses PyTorch-
based deep learning models to correlate objects to absolute depth maps, processed by an
edge server. Spatial data creates system prompts for a cloud language assistant. A voice
activated mobile application facilitates communication with the language model while users
wear the glasses, allowing them to ask navigational questions. Intel’s OpenVINO toolkit is
compatible, compressing algorithms and protecting data through local computation.
We’re conducting experiments on depth and object classification precision. We hope to
deploy SightLine’s AI pipeline on Intel’s DevCloud once refined, to allow online citizen testing
through a web interface, advancing the model to a user-ready state for the visually impaired
worldwide.

## System Architecture

![System Architecture Diagram](/architecture.png)

## Advanced Object Detection
- Currently, training novel object detectors (e.g. YOLOv11, RFDETR) on high-volume datasets, to enhance object detection accuracy and improve computational efficiency. Seeking to increase model's precision for identifying key navigational obstructions such as doorways, staircases, etc.

## Intel Hardware Technologies
- YOLOv8 model compute power offloaded onto Intel x86 CPU chip (Intel Core i7) for
processing on primary edge device during pipeline construction and evaluation,
demonstrating faster computation times than competitive GPUs, while reducing load on
system.
- Our go to market strategy revolves around deploying our tested AI pipeline as a web
interface, due to their accelerated deep learning inference capabilities, that are critical for SightLine's instant detection and
conversion of visual data into information for the LLM.

## Intel Software Technologies
- Intel's OpenVINO toolkit is a critical software tool that we are continuing to
learn/implement to speed up computation 'on the edge' in order to improve usability for the
blind/visually impaired. Intel Neural Compressor's post-training INT8 quantization reduces
YOLOv8 memory storage on device, and speeds up inference an estimated 2-4x for indoor
common object detection. The Microsoft COCO (Common Objects in Context) validation
folder was used as the calibration dataset for Intel Neural Compressor.
- We experimented with OpenVINO runtime to test converted ONNX format and understand
differences in capability compared to the raw PyTorch weights file. NNCF (Neural Network
Compression Framework) was also tested as a quantization approach.
- For further research on SightLine, we plan on leveraging the Intel extension for
transformers, and Optimum for Intel, to compress large language models and attempt local
mobile device processing of SightLine's AI pipeline. The effects of these Intel toolsets can
be examined in an ablation study.

## Measures to address ethical and privacy concerns
### Planning:
- During the planning stages, we stressed the importance of building a solution that
promotes equity and inclusion, driven by the fact that while AI is rapidly advancing, it can be
difficult to implement in technologies for the disabled due to high costs and a lack of trust
around data privacy.
- We planned our project around being reliable for the visually impaired/blind by narrowing
the scope to a specific problem (indoor navigation). Implementing an AI solution in indoor
environments also enhances the security and protection of the hardware behind the system.
### Development:
- We researched the utilization of Intel-powered techniques such as quantization to reduce
the computational load of our model's processing, saving energy and lowering
environmental costs.
- Instead of directly streaming real image data of a user's day to day life to the cloud hosted
large language model (which could be a major privacy concern for many), we built the model
to encode environmental data into basic, un-bias textual data on an edge server. This
decreases direct exposure of private activity to the cloud, since only standardized textual
data is sent to the model.
- An element of respecting human rights and promoting equity and inclusion involves
making the project accessible to different native language speakers. The ElevenLabs API
has robust multi-lingual text-to-speech and speech-to-text capabilities, meaning our model
can be adapted to a global audience seamlessly.
### Deployment:
- Currently, our experimentation and testing of the product focuses on maximizing the
accuracy of depth estimation to make the device safe for usage, and secure. The deployed
variant's hyperparameters are accordingly optimized to adhere to ethical AI principles.
- During usage, the textual prompt generated from the image data is saved as a string
variable, allowing it to be accessed intermediately for users to have full transparency on
what data about their environment is sent to the cloud hosted large language model.
- If migrated to Intel Kubernetes on Tiber AI Cloud, the Gaudi accelerators for object
detection training will have a lower environmental cost than competitor GPU's, reducing
environmental harm during cost intensive model fine tuning.

## References:
- Ackland, Peter, et al. “World Blindness and Visual Impairment: Despite Many Successes, the
Problem Is Growing.” Community Eye Health, vol. 30, no. 100, 2017, pp. 71–73. PubMed
Central, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5820628/.
- Bochkovskii, Aleksei, et al. Depth Pro: Sharp Monocular Metric Depth in Less Than a Second.
arXiv:2410.02073, arXiv, 21 Apr. 2025. arXiv.org, https://doi.org/10.48550/arXiv.2410.02073.
- Guo, Anhong, et al. Toward Fairness in AI for People with Disabilities: A Research Roadmap.
arXiv:1907.02227, arXiv, 2 Aug. 2019. arXiv.org, https://doi.org/10.48550/arXiv.1907.02227.
- Magay, Alexey, et al. A Light and Smart Wearable Platform with Multimodal Foundation
Model for Enhanced Spatial Reasoning in People with Blindness and Low Vision.
arXiv:2505.10875, arXiv, 16 May 2025. arXiv.org,
https://doi.org/10.48550/arXiv.2505.10875.
- Pesudovs, Konrad, et al. “Global Estimates on the Number of People Blind or Visually
Impaired by Cataract: A Meta-Analysis from 2000 to 2020.” Eye, vol. 38, no. 11, Aug. 2024,
pp. 2156–72. www.nature.com, https://doi.org/10.1038/s41433-024-02961-1.
