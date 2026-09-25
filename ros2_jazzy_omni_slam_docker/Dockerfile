FROM ubuntu:24.04

ARG USERNAME=omni_robot
ARG UID=1000
ARG GID=1000

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ROS_DISTRO=jazzy
ENV GZ_VERSION=harmonic

SHELL ["/bin/bash", "-c"]


# ============================================================
# Base OS + ROS repository prerequisites
# ============================================================

RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    ca-certificates \
    curl \
    gnupg2 \
    lsb-release \
    software-properties-common \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# ROS 2 Jazzy repository
# ============================================================

RUN curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
      -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" \
      > /etc/apt/sources.list.d/ros2.list


# ============================================================
# Gazebo Harmonic repository
# ============================================================

RUN curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
      -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" \
      > /etc/apt/sources.list.d/gazebo-stable.list


# ============================================================
# Install ROS 2 / Gazebo / robotics packages
# ============================================================

COPY packages.yml /tmp/packages.yml

RUN apt-get update \
    && grep -Ev '^[[:space:]]*($|#)' /tmp/packages.yml \
       | xargs apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* /tmp/packages.yml


# ============================================================
# Non-root development user
# ============================================================

RUN set -eux; \
    if getent passwd "${UID}" >/dev/null; then \
        EXISTING_USER="$(getent passwd "${UID}" | cut -d: -f1)"; \
        echo "UID ${UID} already belongs to ${EXISTING_USER}"; \
        \
        if [ "${EXISTING_USER}" != "${USERNAME}" ]; then \
            EXISTING_HOME="$(getent passwd "${EXISTING_USER}" | cut -d: -f6)"; \
            usermod -l "${USERNAME}" "${EXISTING_USER}"; \
            usermod -d "/home/${USERNAME}" -m "${USERNAME}"; \
            \
            EXISTING_GROUP="$(getent group "${GID}" | cut -d: -f1)"; \
            if [ -n "${EXISTING_GROUP}" ] && [ "${EXISTING_GROUP}" != "${USERNAME}" ]; then \
                groupmod -n "${USERNAME}" "${EXISTING_GROUP}"; \
            fi; \
        fi; \
    else \
        if getent group "${GID}" >/dev/null; then \
            GROUP_NAME="$(getent group "${GID}" | cut -d: -f1)"; \
        else \
            groupadd --gid "${GID}" "${USERNAME}"; \
            GROUP_NAME="${USERNAME}"; \
        fi; \
        \
        useradd \
            --uid "${UID}" \
            --gid "${GROUP_NAME}" \
            --create-home \
            --shell /bin/bash \
            "${USERNAME}"; \
    fi; \
    usermod -aG dialout,video "${USERNAME}"


# ============================================================
# ROS environment + terminal configuration
# ============================================================

RUN cat >> /home/${USERNAME}/.bashrc <<'EOF'

# ============================================================
# Omni Robot Terminal
# ============================================================

export TERM=xterm-256color

# ROS 2 Jazzy
source /opt/ros/jazzy/setup.bash

# Project workspace
source /home/${USERNAME}/ros2_ws/install/setup.bash 2>/dev/null || true

# Gazebo
export GZ_VERSION=harmonic

# ROS 2 middleware
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp


# ============================================================
# Colored file listing
# ============================================================

export LS_COLORS='di=34:ex=32:ln=36:mi=01;31:*.tar=31:*.gz=31:*.zip=31:*.deb=31:*.rpm=31:*.yaml=33:*.yml=33:*.xml=33:*.json=33:*.py=33:*.cpp=33:*.hpp=33:*.h=33:*.sh=32'

alias ls='ls --color=auto'
alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'


# ============================================================
# Green user@hostname + blue path
# ============================================================

PS1='\[\e[32m\]\u@\h\[\e[0m\]:\[\e[34m\]\w\[\e[0m\]\$ '

# ============================================================

EOF


# Make sure the user's home belongs to the non-root user
RUN chown -R ${UID}:${GID} /home/${USERNAME}


# ============================================================
# Switch to non-root user
# ============================================================

USER ${USERNAME}

WORKDIR /home/${USERNAME}/ros2_ws


# ============================================================
# Start Bash
# ============================================================

CMD ["bash"]