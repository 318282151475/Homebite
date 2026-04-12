FROM nginx:1.25-alpine

# remove default config
RUN rm /etc/nginx/conf.d/default.conf

# copy our configs
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
COPY errors/ /etc/nginx/errors/
COPY ../frontend/index.html /usr/share/nginx/html/index.html

# test config is valid before starting
RUN nginx -t

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

