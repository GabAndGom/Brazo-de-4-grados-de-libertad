% PI discreto de un carro (guía 6). Equivalente de pi_discreto.py (diseño y simulación).
% No ejecutado en la PC de desarrollo (sin MATLAB).
b = 1/200;  Ts = 0.025;  p = 0.9;              % mm/(Hz s), s, polo doble de lazo cerrado
G = tf(b*Ts, [1 -1], Ts);                      % planta: integrador discreto (ZOH)
b0 = (2 - 2*p)/(b*Ts);  b1 = (p^2 - 1)/(b*Ts);
Dz = tf([b0 b1], [1 -1], Ts)                   % u(k) = u(k-1) + b0 e(k) + b1 e(k-1)
T = feedback(Dz*G, 1);
polos = pole(T)
step(10*T, 8); grid on; title('PI discreto, escalón de 10 mm (lineal, sin saturación)');
fprintf('b0 = %.1f Hz/mm, b1 = %.1f Hz/mm\n', b0, b1);
