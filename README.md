<h1 align="center">NanoOWL</h1>

<p align="center"><a href="#usage"/>👍 Usage</a> - <a href="#performance"/>⏱️ Performance</a> - <a href="#setup">🛠️ Setup</a> - <a href="#examples">🤸 Examples</a> <br> - <a href="#acknowledgement">👏 Acknowledgment</a> - <a href="#see-also">🔗 See also</a></p>

NanoOWL is a project that optimizes [OWL-ViT](https://huggingface.co/docs/transformers/model_doc/owlvit) to run 🔥 ***real-time*** 🔥 on [NVIDIA Jetson Orin Platforms](https://store.nvidia.com/en-us/jetson/store) with [NVIDIA TensorRT](https://developer.nvidia.com/tensorrt).  NanoOWL also introduces a new "tree detection" pipeline that combines OWL-ViT and CLIP to enable nested detection and classification of anything, at any level, simply by providing text.

<p align="center">
<img src="assets/jetson_person_2x.gif" height="50%" width="50%"/></p>

> Interested in detecting object masks as well?  Try combining NanoOWL with
> [NanoSAM](https://github.com/NVIDIA-AI-IOT/nanosam) for zero-shot open-vocabulary 
> instance segmentation.

## Xuanlin's Notes

### Prerequisites

```bash
pip install tensorrt onnx
pip install git+https://github.com/NVIDIA-AI-IOT/torch2trt

git clone https://github.com/xuanlinli17/nanoowl   
cd nanoowl
pip install -e .
mkdir data
```

### TensorRT Docker Install

Before you perform TensorRT inference, you need to compile models into TensorRT engine. This requires a docker image that contains the `/usr/src/tensorrt/bin/trtexec` binary (or a TensorRT installed at the system level). For the ease of this process, we will use the official TensorRT docker.
- Install docker and nvidia container toolkit, if not already. For nvidia container toolkit, see [this link](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- Checkout the TensorRT docker version at [this link](https://docs.nvidia.com/deeplearning/tensorrt/container-release-notes/index.html#overview). Note that the docker's CUDA Toolkit and TensorRT versions must exactly match the one you are using. To checkout the locally-installed TensorRT version, run `pip show tensorrt`.
- For example, if your CUDA version is 12.1 and your pip's tensorrt version is 8.6.1-post1, run
```bash
docker pull nvcr.io/nvidia/tensorrt:23.07-py3
```

In the above example, you can then use
```bash
docker run -it --rm -v $HOME:$HOME --user $(id -u):$(id -g) --gpus all nvcr.io/nvidia/tensorrt:23.07-py3  bash
```
to enter the TensorRT docker.

### Building TensorRT models

```
# TODO: investigate the impact of fp16 mode

# In local torch environment,
cd nanoowl
python -m nanoowl.build_image_encoder_engine data/owl_image_encoder_large_patch14.engine \
    --model_name google/owlvit-large-patch14 --onnx_path data/owl_image_encoder_large_patch14.onnx
# In TensorRT docker,
/usr/src/tensorrt/bin/trtexec --onnx=data/owl_image_encoder_large_patch14.onnx  \
    --saveEngine=data/owl_image_encoder_large_patch14.engine --fp16  --shapes=image:1x3x840x840

python -m nanoowl.build_image_encoder_engine data/owlv2_image_encoder_base_patch16.engine \
    --model_name google/owlv2-base-patch16-ensemble --onnx_path data/owlv2_image_encoder_base_patch16.onnx
/usr/src/tensorrt/bin/trtexec --onnx=data/owlv2_image_encoder_base_patch16.onnx  \
    --saveEngine=data/owlv2_image_encoder_base_patch16.engine  --fp16  --shapes=image:1x3x960x960

python -m nanoowl.build_image_encoder_engine data/owlv2_image_encoder_large_patch14.engine \
    --model_name google/owlv2-large-patch14-ensemble --onnx_path data/owlv2_image_encoder_large_patch14.onnx
/usr/src/tensorrt/bin/trtexec --onnx=data/owlv2_image_encoder_large_patch14.onnx  \
    --saveEngine=data/owlv2_image_encoder_large_patch14.engine --fp16  --shapes=image:1x3x1008x1008

cd examples
python owl_predict.py     --prompt="[an owl, a glove]"     --threshold=0.1  --nms_threshold=0.3   --image_encoder_engine=../data/owl_image_encoder_large_patch14.engine  --model google/owlvit-large-patch14  --no_roi_align  --profile
python owl_predict.py     --prompt="[an owl, a glove]"     --threshold=0.1  --nms_threshold=0.3   --image_encoder_engine=../data/owlv2_image_encoder_base_patch16.engine  --model google/owlv2-base-patch16-ensemble  --no_roi_align  --profile
python owl_predict.py     --prompt="[an owl, a glove]"     --threshold=0.1  --nms_threshold=0.3   --image_encoder_engine=../data/owlv2_image_encoder_large_patch14.engine  --model google/owlv2-large-patch14-ensemble  --no_roi_align  --profile

python owl_image_folder_predict.py --threshold=0.15  --nms_threshold=0.3  --image_encoder_engine=../data/owlv2_image_encoder_large_patch14.engine  --model google/owlv2-large-patch14-ensemble  --no_roi_align
```



<a id="usage"></a>
## 👍 Usage

You can use NanoOWL in Python like this

```python3
from nanoowl.owl_predictor import OwlPredictor

predictor = OwlPredictor(
    "google/owlvit-base-patch32",
    image_encoder_engine="data/owlvit-base-patch32-image-encoder.engine",
    no_roi_align=True
)

image = PIL.Image.open("assets/owl_glove_small.jpg")

output = predictor.predict(image=image, text=["an owl", "a glove"], threshold=0.1)

print(output)
```

Or better yet, to use OWL-ViT in conjunction with CLIP to detect and classify anything,
at any level, check out the tree predictor example below!

> See [Setup](#setup) for instructions on how to build the image encoder engine.

<a id="performance"></a>
## ⏱️ Performance

NanoOWL runs real-time on Jetson Orin Nano.

<table style="border-top: solid 1px; border-left: solid 1px; border-right: solid 1px; border-bottom: solid 1px">
    <thead>
        <tr>
            <th rowspan=1 style="text-align: center; border-right: solid 1px">Model †</th>
            <th colspan=1 style="text-align: center; border-right: solid 1px">Image Size</th>
            <th colspan=1 style="text-align: center; border-right: solid 1px">Patch Size</th>
            <th colspan=1 style="text-align: center; border-right: solid 1px">⏱️ Jetson Orin Nano (FPS)</th>
            <th colspan=1 style="text-align: center; border-right: solid 1px">⏱️ Jetson AGX Orin (FPS)</th>
            <th colspan=1 style="text-align: center; border-right: solid 1px">🎯 Accuracy (mAP)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="text-align: center; border-right: solid 1px">OWL-ViT (ViT-B/32)</td>
            <td style="text-align: center; border-right: solid 1px">768</td>
            <td style="text-align: center; border-right: solid 1px">32</td>
            <td style="text-align: center; border-right: solid 1px">TBD</td>
            <td style="text-align: center; border-right: solid 1px">95</td>
            <td style="text-align: center; border-right: solid 1px">28</td>
        </tr>
        <tr>
            <td style="text-align: center; border-right: solid 1px">OWL-ViT (ViT-B/16)</td>
            <td style="text-align: center; border-right: solid 1px">768</td>
            <td style="text-align: center; border-right: solid 1px">16</td>
            <td style="text-align: center; border-right: solid 1px">TBD</td>
            <td style="text-align: center; border-right: solid 1px">25</td>
            <td style="text-align: center; border-right: solid 1px">31.7</td>
        </tr>
    </tbody>
</table>

<a id="setup"></a>
## 🛠️ Setup

1. Install the dependencies

    1. Install PyTorch

    2. Install [torch2trt](https://github.com/NVIDIA-AI-IOT/torch2trt)
    3. Install NVIDIA TensorRT
    4. Install the Transformers library

        ```bash
        python3 -m pip install transformers
        ```
    5. (optional) Install NanoSAM (for the instance segmentation example)

2. Install the NanoOWL package.

    ```bash
    git clone https://github.com/NVIDIA-AI-IOT/nanoowl
    cd nanoowl
    python3 setup.py develop --user
    ```

3. Build the TensorRT engine for the OWL-ViT vision encoder

    ```bash
    mkdir -p data
    python3 -m nanoowl.build_image_encoder_engine \
        data/owl_image_encoder_patch32.engine --onnx_path data/tmp_image_encoder.onnx
    
    # enter TensorRT docker if you don't have trtexec installed systemwide

    /usr/src/tensorrt/bin/trtexec --onnx=data/tmp_image_encoder.onnx \
        --saveEngine=data/owl_image_encoder_patch32.engine --fp16  --shapes=image:1x3x768x768
    ```
    

4. Run an example prediction to ensure everything is working

    ```bash
    cd examples
    python3 owl_predict.py \
        --prompt="[an owl, a glove]" \
        --threshold=0.1 \
        --image_encoder_engine=../data/owl_image_encoder_patch32.engine \
        --no_roi_align
    ```

That's it!  If everything is working properly, you should see a visualization saved to ``data/owl_predict_out.jpg``.  

<a id="examples"></a>
## 🤸 Examples

### Example 1 - Basic prediction

<img src="assets/owl_predict_out.jpg" height="256px"/>

This example demonstrates how to use the TensorRT optimized OWL-ViT model to
detect objects by providing text descriptions of the object labels.

To run the example, first navigate to the examples folder

```bash
cd examples
```

Then run the example

```bash
python3 owl_predict.py \
    --prompt="[an owl, a glove]" \
    --threshold=0.1 \
    --image_encoder_engine=../data/owl_image_encoder_patch32.engine \
    --no_roi_align
```

By default the output will be saved to ``data/owl_predict_out.jpg``. 

You can also use this example to profile inference.  Simply set the flag ``--profile``.

### Example 2 - Tree prediction

<img src="assets/tree_predict_out.jpg" height="256px"/>

This example demonstrates how to use the tree predictor class to detect and
classify objects at any level.

To run the example, first navigate to the examples folder

```bash
cd examples
```

To detect all owls, and the detect all wings and eyes in each detect owl region
of interest, type

```bash
python3 tree_predict.py \
    --prompt="[an owl [a wing, an eye]]" \
    --threshold=0.15 \
    --image_encoder_engine=../data/owl_image_encoder_patch32.engine
```

By default the output will be saved to ``data/tree_predict_out.jpg``.

To classify the image as indoors or outdoors, type

```bash
python3 tree_predict.py \
    --prompt="(indoors, outdoors)" \
    --threshold=0.15 \
    --image_encoder_engine=../data/owl_image_encoder_patch32.engine
```

To classify the image as indoors or outdoors, and if it's outdoors then detect
all owls, type

```bash
python3 tree_predict.py \
    --prompt="(indoors, outdoors [an owl])" \
    --threshold=0.15 \
    --image_encoder_engine=../data/owl_image_encoder_patch32.engine
```


### Example 3 - Tree prediction (Live Camera)

<img src="assets/jetson_person_2x.gif" height="50%" width="50%"/>

This example demonstrates the tree predictor running on a live camera feed with
live-edited text prompts.  To run the example

1. Ensure you have a camera device connected

2. Launch the demo
    ```bash
    cd examples/tree_demo
    python3 tree_demo.py ../../data/owl_image_encoder_patch32.engine
    ```
3. Second, open your browser to ``http://<ip address>:7860``
4. Type whatever prompt you like to see what works!  Here are some examples
    - Example: [a face [a nose, an eye, a mouth]]
    - Example: [a face (interested, yawning / bored)]
    - Example: (indoors, outdoors)



<a id="acknowledgement"></a>
## 👏 Acknowledgement

Thanks to the authors of [OWL-ViT](https://huggingface.co/docs/transformers/model_doc/owlvit) for the great open-vocabluary detection work.

<a id="see-also"></a>
## 🔗 See also

- [NanoSAM](https://github.com/NVIDIA-AI-IOT/nanosam) - A real-time Segment Anything (SAM) model variant for NVIDIA Jetson Orin platforms.
- [Jetson Introduction to Knowledge Distillation Tutorial](https://github.com/NVIDIA-AI-IOT/jetson-intro-to-distillation) - For an introduction to knowledge distillation as a model optimization technique.
- [Jetson Generative AI Playground](https://nvidia-ai-iot.github.io/jetson-generative-ai-playground/) - For instructions and tips for using a variety of LLMs and transformers on Jetson.
- [Jetson Containers](https://github.com/dusty-nv/jetson-containers) - For a variety of easily deployable and modular Jetson Containers
