"""
searcher.py

"""
import sys
import logging
log = logging.getLogger(__name__)
log.info('hello logging')

import glob
import face_recognition
import os
import requests
from PIL import Image, ImageDraw
import numpy as np



class SearcherError(Exception):
    pass

class SearchResult(object):
    """
    class to hold the result of a search
    """

    reference = None # what was used to search for
    match = None # item searched for reference
    match_name = None # name of matching item, string
    match_loc = None # location of matching item
    
    def __init__(self,*args,**kwargs):

        self.match_name = args[0]
        self.match_loc = args[1]

        try:
            self.reference = kwargs['reference']
        except KeyError:
            pass

        try:
            self.match = kwargs['match']
        except KeyError:
            pass

    def __str__(self):
        return self.match_name

class Searcher(object):

    known_photo = None
    search_text = None

    photo_match_dir = None

    known_faces = None # filename, face encodings
    known_texts = None
    
    def __init__(self,searchconfig):

        log.debug('Creating Searcher')
        
        # searchconfig should be dict-like with sections
        try:
            searchtext = searchconfig['text']
            #log.debug('searching for ' + searchtext)
            self.search_text = searchtext
            self.initTextSearch()
        except KeyError:
            searchtext = None

        try: 
            searchphoto = searchconfig['photo']
            self.known_photo = searchphoto
            self.initPhotoSearch()
        except KeyError:
            searchphoto = None

        try:
            photo_match = searchconfig['photo match']
            self.photo_match_dir = photo_match
        except KeyError:
            self.photo_match_dir = None
    
    def initPhotoSearch(self):
        # parse all the photos in the search photo dir and get search features
        # expect that each photo in this set contains one face, if there is more
        # than one face, raise an exception.

        # use the name of the photo for naming the faces

        # test if the known photo is a single file,
        if os.path.isfile(self.known_photo):
            files = [self.known_photo]
        else:
            # find all files in the directory
            files = glob.glob(os.path.sep.join([self.known_photo,'*']))

        # run through the list of files and try to open and extract features
        # as well as file base names to use for text ID
        known_faces = [] 
        for _f in files:

            try:
                im = face_recognition.load_image_file(_f)
            except OSError:
                # this case occurs if _f is not an image file
                # keep going in case there's another file we might process
                continue
            
            fname = os.path.splitext(os.path.basename(_f))[0]
            face_encoding = face_recognition.face_encodings(im)

            # require each search photo to have one face only
            if len(face_encoding) > 1:
                msg = 'Known face photos should have only one face. ' +\
                      _f + 'has ' + str(len(face_encoding)) + ' faces.' 
                raise SearcherError(msg)
            elif len(face_encoding) == 0:
                msg = 'No faces found in ' + _f
                raise SearcherError(msg)

            # pack encoding and fname into a list
            # at this point, we know that face_encoding has only one face,
            # so use the first one
            known_faces.append( [fname, face_encoding[0] ] )

        if len(known_faces) == 0:
            raise SearcherError('No image files found in ' + self.known_photo)
            
        # put the known_faces into an attribute
        self.known_faces = known_faces
        
    def searchPhoto(self,
                    im,
                    drawMatchFace = False):
        """
        im has to be a numpy array, that is writable

        drawMatchFace should be set to the name of a file to write

        returns a list of names matching each ID'd face, or 'unknown' if
        the face is unknown

        returns a list of SearchResults for each matched face or unknown
        """

        # check if known_faces features are ready
        if self.known_faces is None:
            raise SearcherError('Known faces features must be initialized')

        # find all the faces in the image
        face_locations = face_recognition.face_locations(im)

        # encode the faces
        # there may be multiple faces in the test image
        # for each item in unknown_face_encodings, there is a corresponding
        # face_locations, so a zip(unknown_face_encodings,face_locations) works
        unknown_face_encodings = face_recognition.face_encodings(im, face_locations)

        # test if the unknown face encodings match the known faces
        matches = []

        unknown_name = 'unknown'

        if drawMatchFace:
            pil_image = Image.fromarray(im)
            draw = ImageDraw.Draw(pil_image)

        # only set if we actually draw a rectange around a matched face
        didDraw = False
            
        for iunknown,unknown_face in enumerate(unknown_face_encodings):

            # this whole logic is too tortured and confused with too many
            # list comprehensions... blegh.
            
            # m is a list of True/False if the unknown_face matches a known
            # face
            m = face_recognition.compare_faces(\
                    [ _kfe[1] for _kfe in self.known_faces ],\
                    unknown_face )

            # any True in m are a match
            # m_name is a list of names or 'unknown' if no face/name is matched
            # to the unknown face found in the image
            # 
            m_name = [ SearchResult( test[1][0] , face_locations[iunknown] ) \
                       if test[0] \
                       else SearchResult( unknown_name, face_locations[iunknown] )\
                       for test in zip(m,self.known_faces) ]

            if drawMatchFace:
                for _m in m_name:
                    log.debug(str(_m))
                    _m.reference = drawMatchFace
                    if _m.match_name is not unknown_name:
                        _m.reference = drawMatchFace
                        log.debug('drawing ' + str(_m))
                        didDraw = True
                        # draw a rectange around the matching face
                        top,right,bottom,left = _m.match_loc
                        #face_locations[iunknown]
                        draw.rectangle( ( ( left,top ), ( right, bottom) ),
                                        outline = (0, 0, 255) )

                        # add a label below the rectange
                        #text_width, text_height = draw.textsize(_m)
                        #draw.rectangle(((left, bottom - text_height - 10),
                        #                (right, bottom)),
                        #               fill=(0, 0, 255),
                        #               outline=(0, 0, 255))
                        #draw.text((left + 6, bottom - text_height - 5),
                        #          _m,
                        #          fill=(255, 255, 255, 255))

                
            matches += m_name

        if drawMatchFace and didDraw:
            del draw
            log.debug('writing ' + drawMatchFace)
            pil_image.save(drawMatchFace)

        # return matching names
        return matches 

    def initTextSearch(self):

        # parse the search text into a list of strings
        known_texts = self.search_text.lower().strip().split()

        self.known_texts = known_texts

    
    def searchText(self,text):

        match = []
        for i,w in enumerate(self.known_texts):
            if w in text.lower():
                match.append( SearchResult(w, i) )

        return match

class TweetSearcher(Searcher):
    """
    a Class to parse tweets returned from tweepy and search for
    photos, text, etc.
    """

    def __init__(self,searchconfig):
        Searcher.__init__(self,searchconfig)

    def searchPhoto(self,
                    im,
                    tweet,
                    drawMatchFace = False):
        
        # get search result from photoSearch base class
        sr = super().searchPhoto(im,drawMatchFace=drawMatchFace)

        # add some metaata to the search results
        for r in sr:
            r.reference = tweet

        return sr
        
    def searchTweet(self,tweet):
        """
        search a tweet for configured search parameters
        tweet is a tweepy Status object or list of tweepy
        status objects

        returns a list of matches
        """

        try:
            m = [ self.searchTweet(_t) for _t in tweet ]
            return m
        except TypeError:
            pass
            
        try:
            tweettext = tweet.text
        except AttributeError:
            tweettext = tweet.full_text
        else:
            tweettext = ''

        # should get empty list if no match
        textmatch = Searcher.searchText(self,tweettext)

        if textmatch:
            log.debug('found match in ' + tweettext)
            # found a text match, write out the match as a text file
            textMatchFile = os.path.sep.join([self.photo_match_dir,
                                              'tweet_'+tweet.id_str + '.txt'])
            with open(textMatchFile,'w') as f:
                f.write(tweettext)
                
        # check if there is an extended_entities attribute which will
        # specifiy multiple media
        try:
            entities = tweet.extended_entities
        except AttributeError:
            entities = tweet.entities

        # extract the media from the entities
        try:
            media = entities['media']
        except KeyError:
            # no media key present, so no media to match
            media = []
            mediamatches = []

        # media is now a list of items we can parse for urls
        for m in media:
            # this assumes the media are photos
            
            url = m['media_url']
            # this assumes an image - need to handle video
            im = Image.open(requests.get(url, stream=True).raw)
            npim = np.asarray(im)
            
            # if url points to a jpeg, everything is hunky dory
            # if url points to a png, the image comesback with an alpha channel
            # which needs to be removed, this is an issue in the dlib library, see:
            # https://github.com/davisking/dlib/issues/128
            npimc = npim[:, :, :3].copy()

            # find all known faces in this image
            if self.photo_match_dir:
                drawFaceName = os.path.sep.join([self.photo_match_dir,
                                                 'tweet_' + tweet.id_str + '.jpg'])
            else:
                drawFaceName = False
                
            mediamatches = self.searchPhoto( npimc,
                                             tweet,
                                             drawMatchFace = drawFaceName)

        # returns a list of matches
        return mediamatches+textmatch
