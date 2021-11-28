# assetto-corsa-real-automatic-gearbox
A Real Automatic Gearbox App for Assetto Corsa


This app is a fork of someone else's work. 

The original work can be found at https://www.racedepartment.com/downloads/more-realistic-automatic-gearbox.33698/

## Goals of the fork  
* Prevent double-downshifts by adding a requirement of ~2.5sec between downshifts. This would give time for the engine to ramp up and offer a nicer experience. Ideally, we'd want to accept double downshifts but skip directly to the -2 or -3 gear to avoid the harshness of multiple throttle blips (not sure if that's possible in AC though? appart from switching to an H pattern gearbox).
* Require a full kickdown (0.95+ gas pedal) to provoke a downshift in eco-mode. Allowing to comfortably ride the torque of the current gear. Most cars with a decent size engine will be happy to let you ride the torque before rather that downshifting. A sensor at the end of the gas pedal travel signals the ECU to drop one or multiple gears.
* Consider the brake pedal exactly like the gas pedal variable is considered to update aggressiveness. As an aggressive braking suggests an aggressive driving too.
* Consider lateral G-meter to prevent the dropping of aggressiveness while cornering (and prevent upshifts). Maintaining the aggressiveness steady between the moment one enters the corner and the moment one exits it.

**None of the goals are currently achieved**
