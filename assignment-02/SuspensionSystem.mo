package SuspensionSystem
  block Actuator
    Modelica.Mechanics.Translational.Interfaces.Flange_a flange_a annotation(
      Placement(transformation(origin = {-50, 10}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {-70, 10}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Mechanics.Translational.Interfaces.Flange_b flange_b annotation(
      Placement(transformation(origin = {30, 10}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {50, 10}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Blocks.Interfaces.RealInput control_in(unit = "N") annotation(
      Placement(transformation(origin = {-12, 48}, extent = {{-20, -20}, {20, 20}}), iconTransformation(origin = {0, 46}, extent = {{-20, -20}, {20, 20}})));

    type CubicSpringConstant = Real(unit = "N/m3");
    type CubicDampingConstant = Real(unit = "N.s3/m3");

    parameter Modelica.Units.SI.TranslationalSpringConstant c1 = 20000 "Linear stiffness of the spring";
    parameter CubicSpringConstant c2 = 200000 "Nonlinear stiffness of the spring" annotation(Evaluate=false);
    parameter Modelica.Units.SI.TranslationalDampingConstant d1 = 1500 "Linear damping coefficient";
    parameter CubicDampingConstant d2 = 6000 "Nonlinear damping coefficient" annotation(Evaluate=false);
    parameter Modelica.Units.SI.Length srel0 = 0.35 "Natural spring length";

    Modelica.Units.SI.Length srel "Relative displacement";
    Modelica.Units.SI.Velocity vrel "Relative velocity";
    Modelica.Units.SI.Force fspring "Spring force";
    Modelica.Units.SI.Force fdamper "Damper force";
    Modelica.Units.SI.Force f "Total actuator force";
  equation
    srel = flange_b.s - flange_a.s;
    vrel = der(srel);
    fspring = c1*(srel - srel0) + c2*(srel - srel0)^3;
    fdamper = d1*vrel + d2*(vrel)^3;
    f = fspring + fdamper + control_in;
    flange_a.f = -f;
    flange_b.f = f;
  end Actuator;

  block gravity_mass
    parameter Modelica.Units.SI.Mass m "Mass";
    Modelica.Mechanics.Translational.Components.Mass mass(m = m, v(start = 0), a(start = 0), L = 0, stateSelect = StateSelect.prefer) annotation(
      Placement(transformation(extent = {{-10, -10}, {10, 10}})));
    Modelica.Mechanics.Translational.Sources.ConstantForce constantGravityForce(f_constant = -(m*Modelica.Constants.g_n), useSupport = false) annotation(
      Placement(transformation(origin = {-42, -36}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Mechanics.Translational.Interfaces.Flange_a flange_a annotation(
      Placement(transformation(origin = {-100, 0}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {-100, 0}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Mechanics.Translational.Interfaces.Flange_b flange_b annotation(
      Placement(transformation(origin = {100, 0}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {100, 0}, extent = {{-10, -10}, {10, 10}})));
  equation
    connect(mass.flange_a, flange_a) annotation(
      Line(points = {{-10, 0}, {-100, 0}}, color = {0, 127, 0}));
    connect(mass.flange_b, flange_b) annotation(
      Line(points = {{10, 0}, {100, 0}}, color = {0, 127, 0}));
    connect(mass.flange_b, constantGravityForce.flange) annotation(
      Line(points = {{10, 0}, {20, 0}, {20, -36}, {-32, -36}}, color = {0, 127, 0}));
  end gravity_mass;

  model ActuatorTestBench
    parameter Real c2 = 200000 "Nonlinear spring stiffness" annotation(Evaluate=false);
    parameter Real d2 = 6000 "Nonlinear damping coefficient" annotation(Evaluate=false);
    Actuator actuator(c2=c2, d2=d2) annotation(
      Placement(transformation(origin = {-32, 20}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Mechanics.Translational.Sources.Position hydraulicPress(exact = true)  annotation(
      Placement(transformation(origin = {-26, -2}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Mechanics.Translational.Components.Fixed fixedFrame annotation(
      Placement(transformation(origin = {-70, 32}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Blocks.Sources.CombiTimeTable motionProfile(table = [0, 0.35; 1, 0.05; 2, 0.35])  annotation(
      Placement(transformation(origin = {-64, -8}, extent = {{-10, -10}, {10, 10}})));
    Modelica.Blocks.Sources.Constant constantForce(k = 0)  annotation(
      Placement(transformation(origin = {-50, 56}, extent = {{-10, -10}, {10, 10}})));
  equation
    connect(fixedFrame.flange, actuator.flange_a) annotation(
      Line(points = {{-70, 32}, {-38, 32}, {-38, 22}}, color = {0, 127, 0}));
    connect(hydraulicPress.flange, actuator.flange_b) annotation(
      Line(points = {{-16, -2}, {-13, -2}, {-13, 22}, {-26, 22}}, color = {0, 127, 0}));
    connect(motionProfile.y, hydraulicPress.s_ref) annotation(
      Line(points = {{-52, -8}, {-38, -8}, {-38, -2}}, color = {0, 0, 127}));
    connect(constantForce.y, actuator.control_in) annotation(
      Line(points = {{-38, 56}, {-32, 56}, {-32, 24}}, color = {0, 0, 127}));
    annotation(
      experiment(StartTime = 0, StopTime = 2, Tolerance = 1e-06, Interval = 0.002));
  end ActuatorTestBench;

  model QuarterCarPlant
  Modelica.Blocks.Sources.CombiTimeTable roadProfile(table = [0, 0.00; 5, 0.00; 9, 0.08; 12, 0.08; 16, 0.00; 18, 0.00; 19.5, 0.05; 20, 0.00; 21.5, 0.05; 22, 0.00; 24, 0.00; 28, -0.05; 30, -0.05; 35, 0.00; 40, 0.00])  annotation(
      Placement(transformation(origin = {-8, -94}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Mechanics.Translational.Sources.Position roadSurface(f_crit = 0.8)  annotation(
      Placement(transformation(origin = {-8, -64}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Mechanics.Translational.Components.Spring tireSpring(c = 200000, s_rel0 = 0.3)  annotation(
      Placement(transformation(origin = {-8, -38}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  gravity_mass wheelHub(m = 40)  annotation(
      Placement(transformation(origin = {-8, -12}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Actuator actuator annotation(
      Placement(transformation(origin = {-8, 16}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Blocks.Sources.Constant suspensionOff(k = 0)  annotation(
      Placement(transformation(origin = {-46, 16}, extent = {{-10, -10}, {10, 10}})));
  gravity_mass carChassis(m = 300)  annotation(
      Placement(transformation(origin = {-8, 42}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Mechanics.Translational.Components.SpringDamper cabinSeat(c = 40000, d = 1000, s_rel0 = 0.10)  annotation(
      Placement(transformation(origin = {-8, 72}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  gravity_mass lowerBody(m = 24)  annotation(
      Placement(transformation(origin = {-8, 102}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Mechanics.Translational.Components.SpringDamper spine(c = 70000, d = 1500, s_rel0 = 0.45)  annotation(
      Placement(transformation(origin = {-8, 132}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  gravity_mass upperTorso(m = 14)  annotation(
      Placement(transformation(origin = {-8, 164}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Mechanics.Translational.Components.SpringDamper neck(c = 34000, d = 230, s_rel0 = 0.25)  annotation(
      Placement(transformation(origin = {-40, 198}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  gravity_mass head(m = 5.1)  annotation(
      Placement(transformation(origin = {-40, 236}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Mechanics.Translational.Components.SpringDamper shoulders(c = 6400, d = 61, s_rel0 = 0.45)  annotation(
      Placement(transformation(origin = {20, 198}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  gravity_mass arms(m = 7.2)  annotation(
      Placement(transformation(origin = {20, 236}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
    initial equation
        wheelHub.mass.v = 0;
        wheelHub.mass.a = 0;
        carChassis.mass.v = 0;
        carChassis.mass.a = 0;
        lowerBody.mass.v = 0;
        lowerBody.mass.a = 0;
        upperTorso.mass.v = 0;
        upperTorso.mass.a = 0;
        head.mass.v = 0;
        head.mass.a = 0;
        arms.mass.v = 0;
        arms.mass.a = 0;
        
        der(tireSpring.s_rel) = 0;
        der(cabinSeat.s_rel) = 0;
        der(spine.s_rel) = 0;
        der(neck.s_rel) = 0;
        der(shoulders.s_rel) = 0;
  equation
  connect(roadSurface.flange, tireSpring.flange_a) annotation(
      Line(points = {{-8, -54}, {-8, -48}}, color = {0, 127, 0}));
  connect(roadProfile.y[1], roadSurface.s_ref) annotation(
      Line(points = {{-8, -83}, {-8, -76}}, color = {0, 0, 127}));
  connect(tireSpring.flange_b, wheelHub.flange_a) annotation(
      Line(points = {{-8, -28}, {-8, -22}}, color = {0, 127, 0}));
  connect(wheelHub.flange_b, actuator.flange_a) annotation(
      Line(points = {{-8, -2}, {-8, 5}, {-9, 5}, {-9, 9}}, color = {0, 127, 0}));
  connect(actuator.flange_b, carChassis.flange_a) annotation(
      Line(points = {{-8, 22}, {-8, 32}}, color = {0, 127, 0}));
  connect(suspensionOff.y, actuator.control_in) annotation(
      Line(points = {{-35, 16}, {-12, 16}}, color = {0, 0, 127}));
  connect(carChassis.flange_b, cabinSeat.flange_a) annotation(
      Line(points = {{-8, 52}, {-8, 62}}, color = {0, 127, 0}));
  connect(cabinSeat.flange_b, lowerBody.flange_a) annotation(
      Line(points = {{-8, 82}, {-8, 92}}, color = {0, 127, 0}));
  connect(lowerBody.flange_b, spine.flange_a) annotation(
      Line(points = {{-8, 112}, {-8, 122}}, color = {0, 127, 0}));
  connect(spine.flange_b, upperTorso.flange_a) annotation(
      Line(points = {{-8, 142}, {-8, 154}}, color = {0, 127, 0}));
  connect(upperTorso.flange_b, neck.flange_a) annotation(
      Line(points = {{-8, 174}, {-40, 174}, {-40, 188}}, color = {0, 127, 0}));
  connect(neck.flange_b, head.flange_a) annotation(
      Line(points = {{-40, 208}, {-40, 226}}, color = {0, 127, 0}));
  connect(upperTorso.flange_b, shoulders.flange_a) annotation(
      Line(points = {{-8, 174}, {20, 174}, {20, 188}}, color = {0, 127, 0}));
  connect(shoulders.flange_b, arms.flange_a) annotation(
      Line(points = {{20, 208}, {20, 226}}, color = {0, 127, 0}));
    annotation(
      experiment(StartTime = 0, StopTime = 40, Tolerance = 1e-06, Interval = 0.002));
  end QuarterCarPlant;

  annotation(
    uses(Modelica(version = "4.1.0")));
end SuspensionSystem;
