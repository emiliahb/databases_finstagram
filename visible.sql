SELECT photoID, postingDate from photo WHERE allFollowers=1 AND photoPoster in (SELECT username_followed FROM `follow` WHERE username_follower="TestUser") ORDER BY postingDate DESC
