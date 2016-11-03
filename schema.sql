CREATE DATABASE photoshare;
USE photoshare;
#DROP TABLE Pictures CASCADE;
#DROP TABLE Users CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    firstname varchar(255),
    lastname varchar(255),
    birthday varchar(255),
    hometown varchar(255),
    gender varchar(255),
    contribution int4 NOT NULL default 0,
    PRIMARY KEY (user_id)
  #CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Albums
(
  album_id int4   AUTO_INCREMENT,
  name varchar(255),
  user_id int4,
  create_date datetime default CURRENT_TIMESTAMP,
  PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  album_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  num_likes int4 NOT NULL default 0,
  #INDEX upid_idx (user_id),
  #CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  PRIMARY KEY (picture_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE
);

CREATE TABLE Tags
(
  tag_id int4 AUTO_INCREMENT,
  tag_text varchar(255),
  PRIMARY KEY (tag_id)
);

CREATE TABLE Comments
(
  comment_id int4  AUTO_INCREMENT,
  comment_text varchar(255),
  user_id int4,
  picture_id int4,
  create_date datetime default CURRENT_TIMESTAMP,
  PRIMARY KEY (comment_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE own
(
  user_id int4 NOT NULL,
  album_id int4,
  PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE
);

CREATE TABLE leaveComments
(
  picture_id int4 NOT NULL,
  comment_id int4 NOT NULL,
  PRIMARY KEY (comment_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  FOREIGN KEY (comment_id) REFERENCES Comments(comment_id) 
);

CREATE TABLE associatedWith
(
  picture_id int4,
  tag_text varchar(255),
  PRIMARY KEY (picture_id, tag_text),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE friendTo
(
  user1_id int4 NOT NULL,
  user2_id int4 NOT NULL,
  PRIMARY KEY (user1_id, user2_id),
  FOREIGN KEY (user1_id) REFERENCES Users(user_id),
  FOREIGN KEY (user2_id) REFERENCES Users(user_id)
);

CREATE TABLE storeIn
(
  picture_id int4 NOT NULL,
  album_id int4 NOT NULL,
  PRIMARY KEY (picture_id, album_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE
);

