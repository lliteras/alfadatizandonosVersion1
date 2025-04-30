FROM python:3.7-bullseye

RUN apt-get update --fix-missing && apt install --no-install-recommends -y libjpeg-dev zlib1g-dev \
    libreadline-dev\
    libbz2-dev\
    libedit-dev\
    libffi-dev\
    libssl-dev\
    libpq-dev\
    lzma-dev\
    default-jdk\
    gettext\
    libnss-wrapper


RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o run.sh
RUN chmod 744 run.sh
RUN ./run.sh -y
RUN rm run.sh

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN mkdir -p venv log /tmp/.ivy /tmp/py /.wdm /.cache/dconf /.mozilla/firefox/profiles/my-profile /.cache/matplotlib /.config/matplotlib
RUN touch log/error.log log/access.log geckodriver.log

RUN chown -R 1000170000 venv /tmp/py /tmp/.ivy log/error.log log/access.log geckodriver.log /.wdm /.cache/dconf /.mozilla /.cache/matplotlib /.config/matplotlib

USER 1000170000

ENV VIRTUAL_ENV=venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip3 install --no-cache-dir -r requirements.txt

#troubleshooting
USER 0
RUN apt-get update --fix-missing && apt install --no-install-recommends -y nano

COPY --chown=1000170000 ./app .

EXPOSE 5000

COPY --chown=1000170000 passwd.template /tmp/

RUN mkdir /tmp/user

USER 1000170000
RUN export USER_ID=$(id -u) && \
export GROUP_ID=$(id -g) && \
export HOME=/tmp/user &&\
envsubst < /tmp/passwd.template > /tmp/passwd

CMD envsubst < config.py.template > config.py && \
    envsubst < resources/home.py.template > resources/home.py && \
    envsubst < resources/educational_establishments/extracting_data.py.template > resources/educational_establishments/extracting_data.py && \
    gunicorn index:app -b 0.0.0.0:5000 \
    --workers "$NUM_WORKERS" \
    --timeout "$TIMEOUT" \
    --keep-alive "$KEEP_ALIVE" \
    --capture-output \
    --log-level debug \
    --error-logfile log/error.log --access-logfile log/access.log