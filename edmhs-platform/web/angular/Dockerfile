FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npx ng build
FROM nginx:1.27-alpine
COPY --from=build /app/dist/gpcs-r/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
