client_max_body_size 0;

server {
    listen ${LISTEN_PORT};

    client_max_body_size 0;
    client_body_buffer_size 32k;

    location /static {
        alias /vol/static;
    }

    location / {
        uwsgi_pass           ${APP_HOST}:${APP_PORT};
        include              /etc/nginx/uwsgi_params;
        uwsgi_read_timeout 300s;
        uwsgi_send_timeout 300s;
    }
}