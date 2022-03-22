FROM node:14-slim as base

WORKDIR /app

COPY package.json package.json
COPY yarn.lock yarn.lock

RUN yarn

FROM base as production

# install pm2

RUN yarn global add pm2

COPY . .

RUN yarn build
