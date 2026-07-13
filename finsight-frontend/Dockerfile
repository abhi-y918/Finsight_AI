# finsight-frontend/Dockerfile
# ─────────────────────────────────────────────────────────────────
# MULTI-STAGE BUILD
#
# Stage 1 (build): Node.js compiles React → static HTML/CSS/JS files
# Stage 2 (serve): Nginx serves those static files
#
# WHY MULTI-STAGE?
#   Node.js image is ~400MB. Nginx image is ~25MB.
#   We only need Node to BUILD, not to RUN.
#   Final image is tiny — only Nginx + built files.
# ─────────────────────────────────────────────────────────────────

# ── Stage 1: Build ───────────────────────────────────────────────
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files FIRST (before source code)
# WHY? Docker caches layers. If package.json didn't change,
# Docker skips npm install on next build — much faster.
COPY package.json package-lock.json* ./
RUN npm install

# Now copy source code
COPY . .

# Build argument — passed from docker-compose
# VITE_API_URL tells the frontend where the backend lives
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Build React → /app/dist (static files)
RUN npm run build

# ── Stage 2: Serve ───────────────────────────────────────────────
FROM nginx:alpine

# Copy built files from Stage 1 into Nginx's serve directory
COPY --from=build /app/dist /usr/share/nginx/html

# Custom Nginx config for React Router (SPA)
# WHY try_files?
#   Without this, refreshing /dashboard gives 404
#   because Nginx looks for a file called "dashboard" — it doesn't exist.
#   try_files tells Nginx: if file not found, serve index.html
#   React Router then handles the URL client-side.
RUN echo 'server { \
    listen 80; \
    server_name _; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    # Health check endpoint for Docker \
    location /health { \
        return 200 "ok"; \
        add_header Content-Type text/plain; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
