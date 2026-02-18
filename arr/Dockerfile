FROM contre95/soulsolid:v0.20.2

# RUN apk add yt-dlp
# RUN --mount=type=ssh git clone https://git.sr.ht/~canuslector/soulsolid-youtube-plugin /tmp/plugin/youtube
# WORKDIR /tmp/plugin/youtube
# RUN go mod edit -replace=github.com/contre95/soulsolid=/app
# RUN go mod tidy
# RUN go build -buildmode=plugin -o /app/plugins/youtube/plugin.so .

RUN --mount=type=ssh git clone https://git.sr.ht/~canuslector/soulsolid-deemix-plugin /tmp/plugin/deemix
WORKDIR /tmp/plugin/deemix
RUN go mod edit -replace=github.com/contre95/soulsolid=/app
RUN go mod tidy
RUN go build -buildmode=plugin -o /app/plugins/deemix/plugin.so .

WORKDIR /app
