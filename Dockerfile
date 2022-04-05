FROM python:3.7-bullseye

RUN apt update && apt install -y libjpeg-dev zlib1g-dev \
    libreadline-dev\
    libbz2-dev\
    libedit-dev\
    libffi-dev\
    libssl-dev\
    libpq-dev\
    lzma-dev\
    default-jdk

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o run.sh
RUN chmod 744 run.sh
RUN ./run.sh -y

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN mkdir venv  
RUN mkdir log
RUN touch log/error.log
RUN touch log/access.log
RUN chown 1000140001 venv log/error.log log/access.log

USER 1000140001

COPY ./CeoDatumEnv .

ENV VIRTUAL_ENV=venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD gunicorn index -b 0.0.0.0:5000 --error-logfile log/error.log --access-logfile log/access.log