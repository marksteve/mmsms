new Vue({
  el: '#app',
  data: {
    newMember: {
      name: "",
      number: "",
    },
    members: [
      {name: "Steve", number: "09175246984"},
      {name: "Big Bert", number: "09175246984"},
      {name: "Little John", number: "09175246984"},
    ],
  },
  methods: {
    addMember: function() {
      var name = this.newMember.name
      var number = this.newMember.number
      if (name.length && number.length) {
        this.members.push({
          name: name,
          number: number,
        })
        this.newMember.name = ""
        this.newMember.number = ""
      }
    },
    removeMember: function(index) {
      this.members.splice(index, 1)
    },
  },
})
