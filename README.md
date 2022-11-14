## OpenForestMonitor: An Advanced Open-source Deforestation Monitoring System

### 1. Demo
A web-based deforestation system can be linked here: http://183.66.154.42:8501 (the maximum  upload image size is 4GB.)
Attention: this system was deployed in Chongqing, China, so as to access to this website, you need to enable VPN to access! 

#### 1.1 source code
Our paper is under review, after our paper is accepted, we will open source all codes. If you are interested in our work, please contact us with wang749195@outlook.com.

### 2. Performance
For a 91976×74237 pixels image, our server computer with AMD 3900x and 32gb memory can be finished in half a hour.

### 3. Installation
you should use pip tool to install packages. all package can be seen in requirement.txt

recommendation：use Anaconda software to manage third-party packages.

### 4. Citation
@article{wang2022OpenForestMonitor,
  title={{OpenForestMonitor}: An Advanced Open-source Deforestation Monitoring System},
  author={Zhipan Wang, Di Liu, Weihua Pu, Xiang Liao, Qingling Zhang},
  journal={},
  year={2022}
}


a simple way to run the source code, only one line code is needed!
```python 
streamlit run deforestation_Monitor.py  --server.maxUploadSize 4000
```
