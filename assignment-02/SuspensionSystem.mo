package SuspensionSystem
  block Actuator
    Modelica.Mechanics.Translational.Interfaces.Flange_a flange_a annotation(
      Placement(transformation(origin = {-50, 10}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {-70, 10}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Mechanics.Translational.Interfaces.Flange_b flange_b annotation(
      Placement(transformation(origin = {30, 10}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {50, 10}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Blocks.Interfaces.RealInput control_in(unit = "N") annotation(
      Placement(transformation(origin = {-12, 48}, extent = {{-20, -20}, {20, 20}}), iconTransformation(origin = {0, 46}, extent = {{-20, -20}, {20, 20}})));
    // types - couldn't find the conforming unit from the library
    type CubicSpringConstant = Real(unit = "N/m3");
    type CubicDampingConstant = Real(unit = "N.s3/m3");
    // parameters
    parameter Modelica.Units.SI.TranslationalSpringConstant c1 = 20000 "Linear stiffness of the spring";
    parameter CubicSpringConstant c2 = 0 "Nonlinear stiffness of the spring";
    //set to 0, later to be found by estimation
    parameter Modelica.Units.SI.TranslationalDampingConstant d1 = 1500 "Linear damping coefficient";
    parameter CubicDampingConstant d2 = 0 "Nonlinear damping coefficient";
    //again, set to 0, later to be found by estimation
    parameter Modelica.Units.SI.Length srel0 = 0.35 "Natural spring length"; 
    // could also use Position but Length seemed more appropriate because srel0 represents springs natural length
    // vars
    Modelica.Units.SI.Length srel "Relative displacement"; 
    Modelica.Units.SI.Velocity vrel "Relative velocity";
    Modelica.Units.SI.Force fspring "Spring force";
    Modelica.Units.SI.Force fdamper "Damper force";
    //Fact == control_in
    Modelica.Units.SI.Force f "Total actuator force";
  equation
    srel = flange_b.s - flange_a.s;
    vrel = der(srel);
    fspring = c1*(srel - srel0) + c2*(srel - srel0)^3;
    fdamper = d1*vrel + d2*(vrel)^3;
    f = fspring + fdamper + control_in; //Fact == control_in
    flange_a.f = -f;
    flange_b.f = f;
  end Actuator;
  annotation(
    uses(Modelica(version = "4.1.0")));
end SuspensionSystem;
