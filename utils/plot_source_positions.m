% load from text
fid = fopen('SRC.LOC');
data = textscan(fid, '%d%f%f%f');
fclose(fid);

% shape data
xyz = cell2mat(data(2:4));

% plot
plot3(xyz(:, 1), xyz(:, 2), xyz(:, 3), 'markersize', 3, 'marker', 'o', 'color', 'k', 'markerfacecolor', 0*[1 1 1]);
xlabel('x (m)'); ylabel('y (m)'); zlabel('z (m)');

% format plot
title(sprintf('num points: %d', size(xyz, 1)));
grid on, grid minor,
axis equal
