# Sourced by every interactive bash shell in the container (via /etc/bash.bashrc).

# Only for interactive shells.
case $- in *i*) ;; *) return ;; esac

export TERM=xterm-256color

# ROS 2 Jazzy + project workspace
source /opt/ros/jazzy/setup.bash
[ -f "$HOME/ros2_ws/install/setup.bash" ] && source "$HOME/ros2_ws/install/setup.bash"
[ -f /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash ] && \
    source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash

# Middleware / DDS config (written by the entrypoint for this host's network)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
[ -z "${CYCLONEDDS_URI:-}" ] && [ -f /tmp/cyclonedds.xml ] && export CYCLONEDDS_URI=file:///tmp/cyclonedds.xml
export GZ_VERSION=harmonic

# Persistent bash history (directory is bind-mounted from the host)
export HISTFILE="$HOME/.history/bash_history"
export HISTSIZE=100000
export HISTFILESIZE=200000
shopt -s histappend
PROMPT_COMMAND="history -a; history -n${PROMPT_COMMAND:+; $PROMPT_COMMAND}"

# Workspace shortcuts
alias cb='cd ~/ros2_ws && colcon build --symlink-install && source ~/ros2_ws/install/setup.bash'
alias cbr='cd ~/ros2_ws && rm -rf build/* install/* log/*'
alias sl='ros2 launch mecanum_bot bot.launch.py'

# Hybrid NVIDIA laptops: render a command on the dGPU, e.g. `nvrun ros2 launch ...`
command -v nvidia-smi >/dev/null && alias nvrun='__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia'

# Ubuntu's default colour palette, plus project-specific file types on top
eval "$(dircolors -b)"
export LS_COLORS="${LS_COLORS}:*.yaml=33:*.yml=33:*.xml=33:*.json=33:*.urdf=33:*.sdf=33:*.xacro=33:*.py=33:*.cpp=33:*.hpp=33:*.h=33:*.launch.py=1;33:*.sh=32"
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias diff='diff --color=auto'
alias ls='ls --color=auto'
alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'

# Ubuntu-style prompt: bold green user@host, bold blue path
PS1='\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]\$ '
