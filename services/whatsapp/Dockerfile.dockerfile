FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Create sessions directory
RUN mkdir -p /app/sessions

CMD ["node", "index.js"]