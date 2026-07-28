# goals

- [ ] Events

  - [ ] Tutorate: Wann, wo – Weiteres nach Bedarf
    - [ ] TODO: add recurring event for "Tutorate"
  - [x] Besseres Design der Events
    - [ ] fix css oopsie in event list (thumbnail positioning)
  - [x] Recurring events
    - [ ] TODO: testing, show clearer distinction?

- [ ] Tipps & Tricks: unsere Sammlung an Links und Infos

  - [x] Verwalten von Tipps & Tricks durch Studierende
  - [x] Liken von Tipps & Tricks
  - [ ] Kommentieren
    - [ ] Liken von Kommentaren
      - [ ] Kommentieren
        - [ ] Liken von kommentierten Kommentaren
          - [ ] Kommentieren
    - https://github.com/studentenportal/web/issues/104
    - https://github.com/studentenportal/web/issues/76
    - https://github.com/studentenportal/web/issues/63

- [ ] Wünsche/Feedbackformular

# technical

- [ ] updates/upgrades
  - [x] pg 12.2 -> 13 !!1!1
  - [x] test if gunicorn 26.0.0 works in prod
  - [x] server: ubuntu 18.04 -> 26.04
    - [x] ubuntu is a pain in my assholes
  - [ ] secure sshd config on new VM (ansible)
- [x] docker image
  - [x] update python:3.10 (+ remove unnecessary deps?)
  - [x] remove base image completely from web
  - [x] remove/archive base image (github+dockerhub)
- [ ] login problem
  - [ ] add warning message at login that many accounts were deleted; write email
    to team@studentenportal.ch if active account was deleted
- [o] lots of duplicated code between quotes & tipps due to @omega-800 's skill issues
- [ ] svgs instead of fonts for icons
- [ ] i want a cool tux motd on server pwetty pwease (ansible)
- [ ] add robots.txt
- [ ] save email addresses in db in lowercase https://github.com/studentenportal/web/issues/678#issuecomment-5083145263
  - [ ] also migrate the addresses already present

## yeah...

remote: GitHub found 47 vulnerabilities on studentenportal/web's default branch (4 critical, 16 high, 27 moderate). To find out more, visit:
remote: https://github.com/studentenportal/web/security/dependabot
