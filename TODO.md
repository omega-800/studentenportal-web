# goals

- [ ] Events

  - [ ] Tutorate: Wann, wo – Weiteres nach Bedarf
  - [ ] Besseres Design der Events
  - [ ] Recurring events

- [ ] Tipps & Tricks: unsere Sammlung an Links und Infos

  - [ ] Verwalten von Tipps & Tricks durch Studierende
  - [x] Liken von Tipps & Tricks
  - [ ] Kommentieren
    - [ ] Liken von Kommentaren
      - [ ] Kommentieren
        - [ ] Liken von kommentierten Kommentaren
          - [ ] Kommentieren

- [ ] Wünsche/Feedbackformular

# technical

- [ ] update pg 12.2 -> 13 !!1!1
  - [ ] prod: export/backup data, then update, then re-import
    - docker exec -i web_postgres_1 pg_dump -U studentenportal studentenportal > dump.sql
- [ ] test if gunicorn 26.0.0 works in prod
- [ ] update studentenportal/base python:3.10 (+ remove unnecessary deps?)
- [ ] login problem
  - [ ] add warning message at login that many accounts were deleted; write email
    to team@studentenportal.ch if active account was deleted
- [ ] lots of duplicated code between quotes & tipps due to @omega-800 's skill issues
- [ ] svgs instead of fonts for icons
