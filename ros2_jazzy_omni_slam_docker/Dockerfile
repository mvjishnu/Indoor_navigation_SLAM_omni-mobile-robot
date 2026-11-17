# ROS 2 Jazzy + Gazebo Harmonic development image (amd64 / arm64).
#
# Deliberately avoids BuildKit-only syntax (RUN heredocs, --mount, etc.) so it
# builds with both the classic builder and BuildKit/buildx.

FROM ubuntu:24.04

ARG USERNAME=omni_robot
ARG UID=1000
ARG GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    ROS_DISTRO=jazzy \
    GZ_VERSION=harmonic \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# ------------------------------------------------------------
# Base OS + ROS apt repository
# ------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        locales ca-certificates curl gnupg2 lsb-release software-properties-common sudo \
    && add-apt-repository -y universe \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && curl -fsSL --retry 5 https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo "$UBUNTU_CODENAME") main" \
        > /etc/apt/sources.list.d/ros2.list \
    && rm -rf /var/lib/apt/lists/*

# Gazebo Harmonic comes from the ROS repo (ros-jazzy-gz-*-vendor packages,
# pulled in by ros-jazzy-ros-gz), so no separate OSRF repository is needed.

# ------------------------------------------------------------
# ROS 2 / Gazebo / robotics packages (see packages.yml)
# ------------------------------------------------------------
COPY packages.yml /tmp/packages.yml
RUN apt-get update \
    && grep -Ev '^[[:space:]]*($|#)' /tmp/packages.yml | sed 's/[[:space:]]*#.*//' \
       | xargs apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* /tmp/packages.yml \
    && (rosdep init || true)

# ------------------------------------------------------------
# Non-root user matching the host UID/GID (so bind-mounted files stay yours)
# ------------------------------------------------------------
# ubuntu:24.04 ships an "ubuntu" user/group on 1000:1000 -- drop it first.
RUN set -eux; \
    if id ubuntu >/dev/null 2>&1; then userdel -r ubuntu 2>/dev/null || userdel ubuntu; fi; \
    if getent group ubuntu >/dev/null; then groupdel ubuntu; fi; \
    if [ "${UID}" = "0" ]; then echo "Refusing to build with UID 0; build.sh maps root to 1000" >&2; exit 1; fi; \
    if getent passwd "${UID}" >/dev/null; then userdel -r "$(getent passwd "${UID}" | cut -d: -f1)" || true; fi; \
    if getent group "${GID}" >/dev/null; then \
        GROUP_NAME="$(getent group "${GID}" | cut -d: -f1)"; \
    else \
        groupadd --gid "${GID}" "${USERNAME}"; GROUP_NAME="${USERNAME}"; \
    fi; \
    useradd --uid "${UID}" --gid "${GROUP_NAME}" --create-home --shell /bin/bash \
            --groups dialout,video,plugdev,sudo "${USERNAME}" 2>/dev/null \
      || useradd --uid "${UID}" --gid "${GROUP_NAME}" --create-home --shell /bin/bash \
            --groups dialout,video,sudo "${USERNAME}"; \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${USERNAME}"; \
    chmod 0440 "/etc/sudoers.d/${USERNAME}"; \
    mkdir -p "/home/${USERNAME}/ros2_ws/src" "/home/${USERNAME}/.history"; \
    chown -R "${UID}:${GID}" "/home/${USERNAME}"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY ros_bashrc.sh /etc/profile.d/zz-ros.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh \
    && chmod 0644 /etc/profile.d/zz-ros.sh \
    && for rc in /root/.bashrc "/home/${USERNAME}/.bashrc"; do \
         echo '[ -f /etc/profile.d/zz-ros.sh ] && . /etc/profile.d/zz-ros.sh' >> "$rc"; done \
    && chown "${UID}:${GID}" "/home/${USERNAME}/.bashrc"

LABEL omni.uid="${UID}" omni.gid="${GID}"

USER ${USERNAME}
WORKDIR /home/${USERNAME}/ros2_ws

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["sleep", "infinity"]
