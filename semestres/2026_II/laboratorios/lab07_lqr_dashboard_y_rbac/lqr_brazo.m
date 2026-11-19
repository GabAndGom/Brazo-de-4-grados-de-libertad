% LQR discreto del brazo (guía 7), en simulación. Equivalente de lqr_brazo.py.
% Requiere Control System Toolbox (c2d, dlqr, ctrb). No ejecutado en la PC de desarrollo (sin MATLAB).
Ts = 0.025;
bt = 1/(190.3*180/pi);   bxy = 1/200;          % rad/pulso (medido) y mm/pulso (SUPUESTO husillo 5 mm)
A = zeros(3);  C = eye(3);  D = zeros(3, 2);

% Hardware actual: K1 y K2 cerrados, X e Y con el mismo tren
B_actual = [bt 0; 0 bxy; 0 bxy];
sysd = c2d(ss(A, B_actual, C, D), Ts, 'zoh');
fprintf('rango(ctrb(G, H)) = %d de 3\n', rank(ctrb(sysd.A, sysd.B)));
try
    K = dlqr(sysd.A, sysd.B, diag([1/deg2rad(1)^2 1 1]), diag([1/2500^2 1/2500^2]));
    disp('polos de lazo cerrado:'); disp(eig(sysd.A - sysd.B*K));
catch ex
    fprintf('dlqr: %s\n', ex.message);   % el modo sX - sY (autovalor 1) no es estabilizable
end

% Hardware propuesto: un tren por eje
B3 = diag([bt bxy bxy]);
sys3 = c2d(ss(A, B3, C, zeros(3)), Ts, 'zoh');
K3 = dlqr(sys3.A, sys3.B, diag([1/deg2rad(1)^2 1 1]), diag([1 1 1]/2500^2))
polos3 = eig(sys3.A - sys3.B*K3)

% Un carro: x(k+1) = x(k) + Ts*bxy*u(k); u = -K x + Kr r, Kr = K
for rho = [200 500 1000 2000 5000]
    K = dlqr(1, Ts*bxy, 1, 1/rho^2);
    x = 0; xs = zeros(1, 240);
    for k = 1:240
        u = min(max(-K*x + K*10, -5000), 5000);
        xs(k) = x;  x = x + Ts*bxy*u;
    end
    fprintf('rho = %5d Hz/mm: K = %7.1f, polo %.4f, sobreimpulso %.2f %%\n', rho, K, 1 - Ts*bxy*K, max(0, (max(xs)-10)/10*100));
end
