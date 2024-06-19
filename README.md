## A Web-based Prototype System for Deforestation Detection on High-resolution Remote Sensing Imagery with Deep Learning

### 1. Setup

#### 1.1 Third-party Packages Installation
- Environment: Python 3 and above
- In order to run the OpenForestMonitor system, you should install these third-party packages:
```python
pygis
geemap
streamlit
osgeo
onnxruntime
opencv-python
numpy
tqdm
zipfile
multiprocessing
scikit-image
```
- if you have Nvidia GPUs, you can install onnxruntime-gpu to accelerate computing
  
#### 1.2 Deep learning model download
The deforestation model is over 150MB, you can download it from https://drive.google.com/drive/folders/1etsHlRJgT712Oq2HyQ321cFrd_ZkjacU?usp=share_link

And then, copy these models into \Server_Side\RS_change_detection_model.



### 2. Start Client side
To start the Client side, just use one command line:
```python 
streamlit run deforestation_Monitor.py  --server.maxUploadSize 4000
```

### 3. Start Server side
To start the Server side, also only use one command line, as follows:
```python
python main_server.py
```

then, enjoy OpenForestMonitor system!

### 4. Citation
@article{title={OpenForestMonitor: An Advanced Open-source Deforestation Monitoring System},
  author={Zhipan Wang},
  journal={2023},
  year={2023}
}
