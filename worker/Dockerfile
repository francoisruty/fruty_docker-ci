FROM python:2.7

COPY requirements.txt /requirements.txt
#We need this env var, else pyc artefacts remain and pollute code execution
ENV PYTHONDONTWRITEBYTECODE=1
RUN DEBIAN_FRONTEND=noninteractive pip install -r /requirements.txt \
    && apt-get update --fix-missing
