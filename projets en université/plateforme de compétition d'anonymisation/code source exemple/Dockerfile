###########
# BUILDER #
###########

# pull official base image
FROM python:3.7 as builder

# set work directory
WORKDIR /usr/src/DARC

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get install -y \
        gcc \
        build-essential \
        zlib1g-dev \
        wget \
        unzip \
        cmake \
        python3-dev \
        gfortran \
        libblas-dev \
        liblapack-dev \
        libatlas-base-dev \
    && apt-get clean


# install psycopg2 dependencies
RUN apt-get install -y libopenblas-dev gfortran

# lint
RUN pip install --upgrade pip
RUN pip install flake8
COPY . .
RUN flake8 --ignore=E501,F401 ./DARC

# install dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/DARC/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM python:3.7

# create directory for the app user
RUN mkdir -p /home/DARC

# create the app user
RUN groupadd DARC && useradd -g DARC DARC

# create the appropriate directories
ENV HOME=/home/DARC
ENV DARC_HOME=/home/DARC/web
RUN mkdir $DARC_HOME
RUN mkdir $DARC_HOME/static
RUN mkdir $DARC_HOME/media
WORKDIR $DARC_HOME

# install dependencies
RUN apt-get update
COPY --from=builder /usr/src/DARC/wheels /wheels
COPY --from=builder /usr/src/DARC/requirements.txt .
RUN pip install --no-cache /wheels/*

# copy project
COPY . $DARC_HOME

# chown all the files to the app user
RUN chown -R DARC:DARC $DARC_HOME

# change to the app user
USER DARC