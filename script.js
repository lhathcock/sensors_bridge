const express = require('express');
const bodyParser = require('body-parser');
const GPSPosition = require('../models/GPSPosition');
const utils = require('../helpers/utils');
const {check_token} = require("../handlers");
const turf = require("@turf/turf");
const fs = require('fs');

const dotenv = require('dotenv');
dotenv.config();
var env = process.env;
const router = express.Router();

router.use(bodyParser.urlencoded({extended: true}));

router.post('/gpsposition', (req, res) => {
    //Authenticate user
    // console.log(env.AUTHENTICATE);
    // console.log((env.AUTHENTICATE === '1'));
    if (env.AUTHENTICATE === '1') {
        if (!check_token(req)) {
            return res.status(401).end()
        }
    }
    // if (location_code === null) {
    //     return res.status(401).end();
    // }
    res.sendStatus(200);
    var data_proc = {
        createdAt: new Date(),
        updatedAt: new Date(),
    }

    var insert_data = Object.assign(req.body, data_proc);

    var prepped_data = utils.prepare_data(insert_data, 'gpsposition');
    var proc_data2 = {
        point_geom: {
            type: 'Point',
            coordinates: [req.body['longitude'], req.body['latitude']],
            crs: {
                type: "name",
                properties: {
                    name: "urn:ogc:def:crs:EPSG::4326"
                }
            }
        }
    };
    prepped_data = Object.assign(prepped_data, proc_data2);
    var current_update = new Date();
    location_code = null;
    var boat_path = [];
    var boundary;
    // console.log(profile.locations)
    for (var i = 0; i < profile.locations.length; i++) {

            fs.readFile(profile.locations[i].geojson, function (err, data) {
                var pt = turf.point([req.body['longitude'], req.body['latitude']]);
                var poly = turf.bboxPolygon(profile.locations[i].bbox);
                // console.log('Test')
                var curr_code = profile.locations[i].code;
                if (turf.booleanPointInPolygon(pt, poly)) {
            // console.log(locations_boundary);
            var locations_boundary;
            // if (typeof locations_boundary[curr_code] === "undefined") {
            //     continue
            // }


                // console.log(l, curr_code);
                locations_boundary = JSON.parse(data);

                if (locations_boundary.features[0].geometry.type === 'MultiPolygon') {
                    boundary = turf.multiPolygon(locations_boundary.features[0].geometry.coordinates);
                } else if (locations_boundary.features[0].geometry.type === 'Polygon') {
                    console.log(locations_boundary.features[0].geometry);
                    boundary = turf.polygon(locations_boundary.features[0].geometry);
                }
                // var pt_within = turf.pointsWithinPolygon(pt, boundary);
                // console.log(ptsWithin);
                if (turf.pointsWithinPolygon(pt, boundary)) {
                    // continue

                last_update = current_update;
                location_code = curr_code;
                const LocGpsPosition = profile_models[location_code + 'gpsposition'];
                // io.emit('recordadded', {table: 'bosgpsposition', data: insert_data});

                var layer = 'gps_position';
                prepped_data['coordinates'] = [parseFloat(prepped_data['longitude']),
                    parseFloat(prepped_data['latitude'])];

                boat_path.push(prepped_data['coordinates']);
                // boat_datetime = prepped_data['boat_datetime'];
                if (boat_path.length > 3) {
                    boat_path.shift();
                }
                // var {data, layer, p1, p2, angle} = utils.insert_gps_record(
                //     LocGpsPosition, insert_data, boat_path);
                // console.log('GPS added')
                // console.log(insert_data['true_course'])
                io.emit('recordadded', {
                    table: location_code + 'gpsposition', data: prepped_data, layer: layer,
                    boat: [boat_path], angle: parseFloat(prepped_data['true_course'])
                });
                sensor_last_datetime['gpsposition'] = new Date(prepped_data['boat_datetime'] + 'UTC');
                // console.log(prepped_data)
                utils.insert_gps_to_db(LocGpsPosition, prepped_data);
                }
                }
            });

            // break;

    }
    // }

    GPSPosition.create(prepped_data).then(response => {
        // console.log('Saved', 'GPSPosition')

    }).catch(err => console.log());

});
module.exports = router