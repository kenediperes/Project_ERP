FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN mkdir -p sessions
CMD ["node", "index.js"]
