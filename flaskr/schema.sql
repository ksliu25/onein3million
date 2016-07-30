DROP TABLE if exists slideshows;
CREATE TABLE slideshows (
  id integer primary key autoincrement,
  name text not null,
  blurb text,
  description text,
  soundclip_s3_url text not null
);

DROP TABLE if exists photos;
CREATE TABLE photos (
    id integer primary key autoincrement,
    slideshow_id integer not null,
    name text not null,
    soundclip_range integer,
    photo_s3_url text not null,
    FOREIGN KEY(slideshow_id) REFERENCES slideshows(id)
);