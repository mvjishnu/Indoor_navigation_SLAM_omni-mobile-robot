                 Raspberry Pi 4
                     ROS 2
                       │
                  /cmd_vel
                       │
                       ↓
        ┌─────────────────────────┐
        │ mecanum_drive_controller│
        └─────────────────────────┘
                       │
              4 wheel velocities
                  rad/s
                       │
                       ↓
             ros2_control
          hardware interface
                       │
                  USB Serial
                 115200 baud
                       │
                       ↓
                  ESP32-S3
                       │
            Mechanum_Encoder_library
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
         Motor control        Encoders
             ↓                   ↓
          Drivers             ticks
             ↓                   │
           Motors ───────────────┘


The esp32 should recive something like:

FL = 4.2 rad/s
FR = 4.2 rad/s
BR = 4.2 rad/s
BL = 4.2 rad/s

why? because the ros2 mecanum_drive_controller node calculates the mechanum kinematics for you. and gives values in rad/s

For now The Functions are made to test the movements of the mechanum wheels. But we eventually need to build a new funtion to translate them into rad/s or controll each wheel usinf rad/s so it can apply it to the hardware.