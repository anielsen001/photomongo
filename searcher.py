"""
searcher.py

"""

import glob
import face_recognition
import os

class SearcherError(Exception):
    pass

class Searcher(object):

    known_photo = None
    search_text = None

    known_faces = None
    
    def __init__(self,searchconfig):

        # searchconfig should be dict-like with sections
        try:
            searchtext = searchconfig['text']
            self.search_test = searchtext
        except KeyError:
            searchtext = None

        try: 
            searchphoto = searchconfig['photo']
            self.known_photo = searchphoto
            self.initPhotoSearch()
        except KeyError:
            searchphoto = None
    
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
        
    def searchPhoto(self,im):
        """
        im has to be a numpy array, that is writable
        """

        # check if known_faces features are ready
        if self.known_faces is None:
            raise SearcherError('Known faces features must be initialized')

        # find all the faces in the image
        face_locations = face_recognition.face_locations(im)

        # encode the faces
        # there may be multiple faces in the test image
        unknown_face_encodings = face_recognition.face_encodings(im, face_locations)

        # test if the unknown face encodings match the known faces
        matches = []

        unknown_name = 'unknown'
        
        for unknown_face in unknown_face_encodings:
            m = face_recognition.compare_faces(\
                    [ _kfe[1] for _kfe in self.known_faces ],\
                    unknown_face )

            # any True in m are a match
            m_name = [ test[1][0]\
                       if test[0] else unknown_name\
                       for test in zip(m,self.known_faces) ]

            matches += m_name

        # return matching names
        return matches
        

    
