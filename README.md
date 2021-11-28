# assetto-corsa-real-automatic-gearbox
A Real Automatic Gearbox App for Assetto Corsa


This app is a fork of someone else's work. 

The original work can be found at https://www.racedepartment.com/downloads/more-realistic-automatic-gearbox.33698/

## Goals of the fork  
* [x] Prevent double-downshifts by adding a requirement of 2.5sec between downshifts. This would give time for the engine to ramp up and offer a nicer experience. Ideally, we'd want to accept double downshifts but skip directly to the -2 or -3 gear to avoid the harshness of multiple throttle blips (not sure if that's possible in AC though? appart from switching to an H pattern gearbox).
* [x] Consider the brake pedal exactly like the gas pedal variable is considered to update aggressiveness. As an aggressive braking suggests an aggressive driving too.
* [ ] Require a full kickdown (0.95+ gas pedal) to provoke a downshift in eco-mode. Allowing to comfortably ride the torque of the current gear. Most cars with a decent size engine will be happy to let you ride the torque before rather that downshifting. A sensor at the end of the gas pedal travel signals the ECU to drop one or multiple gears.
* [ ] Consider lateral G-meter to prevent the dropping of aggressiveness while cornering (and prevent upshifts). Maintaining the aggressiveness steady between the moment one enters the corner and the moment one exits it.
* [ ] Avoid excessive throttle blips on downshifts (attempt a proper rev match instead, if that's not possible just disable blips if the rpms are mid to low (meaning not aggressive driving) since the blip if a heavy one)
* [ ] Consider the speed at which the gas pedal is actuated as an factor of aggressiveness. Since pressing the gas all the way **slowly** means that we want full torque, not necessarily a downshift. 
* [ ] Prevent downshifts to 1st gear except bellow 10 km/h or when agressiveness is above 0.95
* [ ] Splits the driving modes into distinct algorithms, rather than just altering a few variables (since there is lots of tweaking needed between the differents driving modes)
