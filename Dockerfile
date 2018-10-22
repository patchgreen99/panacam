FROM debian:latest
MAINTAINER Conda Development Team <conda@continuum.io>

ADD ./requirements.txt /tmp/requirements.txt
ADD ./conda_requirements.txt /tmp/conda_requirements.txt
RUN apt-get -qq update && apt-get -qq -y install curl bzip2 unzip \
    && curl -sSL https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -bfp /usr/local \
    && rm -rf /tmp/miniconda.sh \
    && conda install -y python=2 \
    && conda update conda \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && apt-get install -qq -y libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && conda clean --all --yes \
    && conda config --set ssl_verify no \
    && conda config --add channels conda-forge --system \
    && conda install --yes --file /tmp/conda_requirements.txt \
    && pip install -r /tmp/requirements.txt

ENV PATH /opt/conda/bin:$PATH

RUN apt-get -qq update && apt-get -qq -y install curl bzip2 unzip python \
    && curl https://dl.google.com/dl/cloudsdk/channels/rapid/google-cloud-sdk.zip > /tmp/google-cloud-sdk.zip && unzip /tmp/google-cloud-sdk.zip -d /tmp/ && rm /tmp/google-cloud-sdk.zip \
    && /tmp/google-cloud-sdk/install.sh --usage-reporting=true --path-update=true --bash-completion=true --rc-path=/.bashrc \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean

ENV PATH /tmp/google-cloud-sdk/bin:$PATH
ADD ./app.py /tmp/app.py
ADD ./lib /tmp/lib
CMD [ "python", "/tmp/app.py" ]