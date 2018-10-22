FROM debian:latest
MAINTAINER Conda Development Team <conda@continuum.io>

ADD ./requirements.txt /tmp/requirements.txt
ADD ./conda_requirements.txt /tmp/conda_requirements.txt
RUN apt-get -qq update && apt-get -qq -y install curl bzip2 \
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
ADD ./app.py /tmp/app.py
ADD ./lib /tmp/lib
CMD [ "python", "/tmp/app.py" ]