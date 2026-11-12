% Modelo en espacio de estados del brazo XK-JS1-1 (guías 4 y 5). Equivalente de espacio_estados_brazo.py
% Requiere Control System Toolbox (ss, ctrb, obsv, c2d, tf).
% Estado x = [theta (rad); sX (mm); sY (mm)], entrada u = [f0; f1] (Hz, con signo = DIR).
% El sistema es conmutado: K1 (Q0.5) y K2 (Q0.6) eligen a qué carro llega el tren f1.

K_theta = 190.3*180/pi;      % pulsos/rad (medido el 26/10/2026)
K_xy    = 1000/5;            % pulsos/mm (SUPUESTO: husillo de 5 mm)
bt = 1/K_theta;  bxy = 1/K_xy;

A = zeros(3);
Bm = @(k1, k2) [bt 0; 0 k1*bxy; 0 k2*bxy];
C = [0 1 -0.492; 585.4 0 0; 0 0 2.307];   % J(q0) en el centro (0°, 85, 85), manual técnico cap. 8
D = zeros(3, 2);

modos = {[1 0], 'K1 (X)'; [0 1], 'K2 (Y)'; [1 1], 'K1 y K2'; [0 0], 'ninguno'};
for i = 1:size(modos, 1)
    k = modos{i, 1};
    fprintf('%-10s rango(ctrb) = %d\n', modos{i, 2}, rank(ctrb(A, Bm(k(1), k(2)))));
end
fprintf('conmutando: rango([B(K1) B(K2)]) = %d\n', rank([Bm(1, 0) Bm(0, 1)]));
fprintf('rango(obsv) con C = J(centro): %d\n', rank(obsv(A, C)));

sys = ss(A, Bm(1, 1), C, D);
Ts = 0.025;                  % 25 ms: un paquete de 100 pulsos a 4 kHz (ver informe del laboratorio 5)
sysd = c2d(sys, Ts, 'zoh')
G_base  = tf(bt, [1 0])      % Theta(s)/F0(s)
G_carro = tf(bxy, [1 0])     % S(s)/F1(s)
Gz_carro = c2d(G_carro, Ts, 'zoh')
