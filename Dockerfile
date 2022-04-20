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
RUN rm run.sh

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN mkdir venv  
RUN mkdir log
RUN mkdir /tmp/.ivy
RUN mkdir /tmp/py
RUN touch log/error.log
RUN touch log/access.log
RUN chown 1000110000 venv /tmp/py /tmp/.ivy log/error.log log/access.log

RUN apt install -y gettext libnss-wrapper

RUN apt install -y nano

RUN mkdir -p /.config/matplotlib
RUN chown 1000110000 /.config/matplotlib

USER 1000110000

ENV VIRTUAL_ENV=venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip3 install --no-cache-dir -r requirements.txt

COPY --chown=1000110000 ./app .

EXPOSE 5000

COPY --chown=1000110000 passwd /tmp/

#variables $DB_HOST, DB_NAME, $DB_USER, $DB_PASS

CMD envsubst < config.py.template > config.py && \
    envsubst < resources/home.py.template > resources/home.py && \
    envsubst < resources/educational_establishments/extracting_data.py.template > resources/educational_establishments/extracting_data.py && \
    LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libnss_wrapper.so \
    NSS_WRAPPER_PASSWD=/tmp/passwd \
    NSS_WRAPPER_GROUP=/etc/group \
    gunicorn index:app -b 0.0.0.0:5000 \
    --workers "$NUM_WORKERS" \
    --timeout "$TIMEOUT" \
    --keep-alive "$KEEP_ALIVE"\
    --capture-output --log-level debug\
    --error-logfile log/error.log --access-logfile log/access.log