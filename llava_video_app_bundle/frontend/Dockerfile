FROM node:18
WORKDIR /app
COPY package.json .
COPY package-lock.json .
RUN npm install && chmod +x ./node_modules/.bin/react-scripts
COPY . .
CMD ["npm", "start"]
